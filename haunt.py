#!/usr/bin/python

import cv2
import numpy as np

camnum = 2
while True:
    print "trying to access camera number %i" % (camnum)
    cam = cv2.VideoCapture(camnum)
    if cam.read()[0]: break
    if camnum < 0: raise Exception('No camera found')
    camnum -= 1
camwidth = 800
camheight = 600
cam.set(3, camwidth)
cam.set(4, camheight)
def getimg():
    return cam.read()[1]
img = getimg()
shape = height, width, depth = img.shape
print "using camera %i with image %s" % (camnum, str(shape))

ghostloader = cv2.VideoCapture('ghost.avi')
def getghost():
    global ghostloader
    r, ghost = ghostloader.read()
    if True == r : return ghost
    ghostloader = cv2.VideoCapture('ghost.avi')
    return getghost()

downsample = 2
def slim(img):
    for i in range(downsample):
        img = cv2.pyrDown(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, _, img = cv2.split(img)
    return img
slimimg = slim(img)

basesize = 10
def updatebase():
    global base
    base = np.zeros(img.shape)
    for i in range(basesize):
        base += 1.0 * getimg() / basesize
    base = slim(np.uint8(base))
updatebase()

th = 20
noise = 50
blur = 10
aurasize = 100
#FIXME test higher steps
aurasteps = 4
alphamin = 255 % aurasteps
alphastep = 255 / aurasteps
sizestep = aurasize / (aurasteps - 1)
def getmask(base, img):
    mask = cv2.absdiff(base, img)
    _, mask = cv2.threshold(mask, th, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > noise]
    alpha = alphamin
    size = aurasize
    for i in range(aurasteps):
        alpha += alphastep
        if 255 == alpha: size = -1
        cv2.drawContours(mask, contours, -1, alpha, size)
        size -= sizestep
    mask = cv2.blur(mask, (blur, blur))
    for i in range(downsample):
        mask = cv2.pyrUp(mask)
    return mask

import Image
def getblend(img1, img2, mask):
    return np.asarray(Image.composite(
        Image.fromarray(img1),
        Image.fromarray(img2),
        Image.fromarray(mask)
    ))

from multiprocessing import Pool
pool = Pool()
imgresult = pool.apply_async(getimg)
img = imgresult.get()
def updateimg():
    global img, imgresult, slimimg, imgcnt
    if(False == imgresult.ready()): return
    img = imgresult.get()
    imgresult = pool.apply_async(getimg)
    slimimg = slim(img)
    imgcnt += 1

maskresult = pool.apply_async(getmask, (base, slimimg))
mask = maskresult.get()
def updatemask():
    global mask, maskresult, maskcnt
    updateimg()
    if(False == maskresult.ready()): return
    mask = maskresult.get()
    maskresult = pool.apply_async(getmask, (base, slimimg))
    maskcnt += 1

ghostresult = pool.apply_async(getghost)
ghost = ghostresult.get()
def updateghost():
    global ghost, ghostresult, ghostcnt
    if(False == ghostresult.ready()): return
    ghost = ghostresult.get()
    ghostresult = pool.apply_async(getghost)
    ghostcnt += 1

blendresult = pool.apply_async(getblend, (img, ghost, mask))
blend = blendresult.get()
def updateblend():
    global blend, blendresult, blendcnt
    updatemask()
    updateghost()
    if(False == blendresult.ready()): return
    blend = blendresult.get()
    blendresult = pool.apply_async(getblend, (img, ghost, mask))
    blendcnt += 1

def showframe(_):
    updateimg()
    global out
    out = img

def blendframe(_):
    global out
    updateblend()
    out = blend

import pyglet
window = pyglet.window.Window(resizable=True)
from time import time
stime = time()
imgcnt = maskcnt = ghostcnt = blendcnt = 0
out = img
def display(_):
    global stime, imgcnt, maskcnt, ghostcnt, blendcnt
    ctime = time()
    if ctime - stime >= 1:
        print '%.2f fps (%i frames, %i masks, %i ghosts, %i blends)' % (
            pyglet.clock.get_fps(), imgcnt, maskcnt, ghostcnt, blendcnt
        )
        imgcnt = maskcnt = ghostcnt = blendcnt = 0
        stime = ctime

    #window.clear()
    #outr = cv2.resize(out, (window.width, window.height))
    #pyglet.image.ImageData(window.width, window.height, 'bgr', outr.tostring(), -1 * depth * window.width).blit(0, 0)
    pyglet.image.ImageData(width, height, 'bgr', out.tostring(), -1 * depth * width).blit(0, 0)

def unsched():
    pyglet.clock.unschedule(showframe)
    pyglet.clock.unschedule(blendframe)

frameinterval = 1.0 / 20
@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.SPACE:
        updatebase()
        print 'base frame set'
    elif symbol == pyglet.window.key.F:
        window.set_fullscreen(not window.fullscreen)
        print 'toggled fullscreen'
    elif symbol == pyglet.window.key.D:
        unsched()
        pyglet.clock.schedule(showframe)
        print 'showing cam'
    elif symbol == pyglet.window.key.G:
        unsched()
        pyglet.clock.schedule(blendframe)
        print 'showing ghosts'
    elif symbol == pyglet.window.key.ESCAPE:
        print 'terminating processes',
        unsched()
        pool.close()
        pool.join()
        cam.release()
        pyglet.app.exit()

pyglet.clock.schedule(display)
pyglet.app.run()
