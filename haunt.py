#!/usr/bin/python

import cv2
import numpy as np

camnum = 2
while True:
    print "Trying to access camera number %i" % (camnum)
    cam = cv2.VideoCapture(camnum)
    if cam.read()[0]: break
    if camnum < 0: raise Exception('No camera found')
    camnum -= 1
camwidth = 1920
camheight = 1280
cam.set(3, camwidth)
cam.set(4, camheight)
def getimg():
    return cam.read()[1]
img = getimg()
shape = height, width, depth = img.shape
print "Using camera %i with image %s" % (camnum, str(shape))

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
ghost = img
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
    global imgresult, imgcnt, img, slimimg
    if(False == imgresult.ready()): return
    imgcnt += 1
    img = imgresult.get()
    imgresult = pool.apply_async(getimg)
    slimimg = slim(img)

maskresult = pool.apply_async(getmask, (base, slimimg))
mask = maskresult.get()
def updatemask():
    global maskresult, maskcnt, mask
    updateimg()
    if(False == maskresult.ready()): return
    maskcnt += 1
    mask = maskresult.get()
    maskresult = pool.apply_async(getmask, (base, slimimg))

blendresult = pool.apply_async(getblend, (img, ghost, mask))
blend = blendresult.get()
def updateblend():
    global blendresult, blendcnt, blend
    updatemask()
    if(False == blendresult.ready()): return
    blendcnt += 1
    blend = blendresult.get()
    blendresult = pool.apply_async(getblend, (img, ghost, mask))

def showframe(_):
    global blend
    updateimg()
    blend = img

fnum = -1
def saveframe(_):
    global fnum
    showframe(_)
    fnum += 1
    cv2.imwrite("tmp/ghost%03i.png" % (fnum), img)

def loadghost(_):
    global fnum, ghost
    fnum += 1
    img = cv2.imread("tmp/ghost%03i.png" % (fnum))
    if img is None:
        fnum = -1
    else:
        ghost = img

from time import time
stime = time()
loopcnt = imgcnt = maskcnt = blendcnt = 0
def frame(_):
    global stime, loopcnt, imgcnt, maskcnt, blendcnt
    global imgresult, img, slimimg, maskresult, mask, blendresult, blend
    ctime = time()
    loopcnt += 1
    if ctime - stime >= 1:
        print '%.2f fps (%i loops, %i frames, %i masks, %i blends)' % (
            pyglet.clock.get_fps(), loopcnt, imgcnt, maskcnt, blendcnt
        )
        loopcnt = imgcnt = maskcnt = blendcnt = 0
        stime = ctime

    updateblend()

import pyglet
window = pyglet.window.Window(resizable=True)
@window.event
def on_draw():
    window.clear()
    out = cv2.resize(blend, (window.width, window.height))
    pyglet.image.ImageData(window.width, window.height, 'bgr', out.tostring(), -1 * depth * window.width).blit(0, 0)

frameinterval = 1.0 / 25
@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pool.terminate()
        from time import sleep
        sleep(1)
        pyglet.app.exit()
    elif symbol == pyglet.window.key.SPACE:
        updatebase()
    elif symbol == pyglet.window.key.F:
        window.set_fullscreen(not window.fullscreen)
    else:
        pyglet.clock.unschedule(showframe)
        pyglet.clock.unschedule(saveframe)
        if symbol == pyglet.window.key.S:
            print 'Saving ghosts'
            pyglet.clock.schedule_interval(saveframe, frameinterval)
        elif symbol == pyglet.window.key.G:
            pyglet.clock.schedule(frame)
            pyglet.clock.schedule_interval(loadghost, frameinterval)

pyglet.clock.schedule_interval(showframe, 1.0 / 25)
pyglet.app.run()
