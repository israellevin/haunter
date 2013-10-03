#!/usr/bin/python

import cv2
import numpy as np

camnum = 2
camwidth = 640
camheight = 480
while True:
    print "Trying to access camera number %i" % (camnum)
    cam = cv2.VideoCapture(camnum)
    if cam.read()[0]: break
    if camnum < 0: raise Exception('No camera found')
    camnum -= 1
#cam.set(3, camwidth)
#cam.set(4, camheight)
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

basesize = 10
def getbase():
    global base
    base = np.zeros(img.shape)
    for i in range(basesize):
        base += 1.0 * getimg() / basesize
    return np.uint8(base)
base = getbase()
slimbase = slim(base)

th = 20
noise = 50
blur = 10
aurasize = 100
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
    return mask

from multiprocessing import Pool
pool = Pool()
imgresult = pool.apply_async(getimg)
img = imgresult.get()
slimimg = slim(img)
maskresult = pool.apply_async(getmask, (slimbase, slimimg))
mask = maskresult.get()

from time import time
stime = time()
loopcnt = framecnt = maskcnt = 0
def frame(_):
    global stime, framecnt, loopcnt, maskcnt, imgresult, img, slimimg, maskresult, mask

    ctime = time()
    loopcnt += 1
    if ctime - stime >= 1:
        print '%i loops %i frames %i masks' % (loopcnt, framecnt, maskcnt)
        loopcnt = framecnt = maskcnt = 0
        stime = ctime

    if(False == imgresult.ready()): return
    framecnt += 1
    img = imgresult.get()
    imgresult = pool.apply_async(getimg)
    slimimg = slim(img)

    if(False == maskresult.ready()): return
    maskcnt += 1
    mask = maskresult.get()
    maskresult = pool.apply_async(getmask, (slimbase, slimimg))
    for i in range(downsample):
        mask = cv2.pyrUp(mask)

import Image
ghost = Image.open('tmp/ghost001.png')
import pyglet
window = pyglet.window.Window(resizable=True)
@window.event
def on_draw():
    window.clear()
    out = Image.composite(
        Image.fromarray(img),
        ghost,
        Image.fromarray(mask).resize((width, height))
    ).resize((window.width, window.height))
    pyglet.image.ImageData(window.width, window.height, 'bgr', out.tostring(), -1 * depth * window.width).blit(0, 0)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.ESCAPE:
        pool.terminate()
        pyglet.app.exit()
    elif symbol == pyglet.window.key.ENTER:
        pyglet.clock.schedule(frame)
    elif symbol == pyglet.window.key.F:
        window.set_fullscreen(not window.fullscreen)

pyglet.app.run()
