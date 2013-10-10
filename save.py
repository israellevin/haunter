#!/usr/bin/python

import cv2

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

recorder = cv2.VideoWriter('ghost.avi', cv2.cv.FOURCC('M', 'J', 'P', 'G'), 20, (width, height))
def save(img): recorder.write(img)

from multiprocessing import Pool
pool = Pool()
imgresult = pool.apply_async(getimg)
img = imgresult.get()
def updateimg():
    global img, imgresult, imgcnt
    if(False == imgresult.ready()): return
    img = imgresult.get()
    imgresult = pool.apply_async(getimg)
    imgcnt += 1

saveresult = pool.apply_async(save, (img,))
def updatesave():
    global saveresult, savecnt
    if(False == saveresult.ready()): return
    saveresult = pool.apply_async(save, (img,))
    savecnt += 1

def showframe(_):
    updateimg()
    global out
    out = img

def saveframe(_):
    showframe(_)
    updatesave()

import pyglet
window = pyglet.window.Window(resizable=True)
from time import time
stime = time()
imgcnt = savecnt = 0
out = img
def display(_):
    global stime, imgcnt, savecnt
    ctime = time()
    if ctime - stime >= 1:
        print '%.2f fps (%i frames, %i saved)' % (
            pyglet.clock.get_fps(), imgcnt, savecnt
        )
        imgcnt = savecnt = 0
        stime = ctime

    pyglet.image.ImageData(width, height, 'bgr', out.tostring(), -1 * depth * width).blit(0, 0)

def unsched():
    recorder.release()
    pyglet.clock.unschedule(showframe)
    pyglet.clock.unschedule(saveframe)

frameinterval = 1.0 / 20
@window.event
def on_key_press(symbol, modifiers):
    if symbol == pyglet.window.key.D:
        unsched()
        pyglet.clock.schedule(showframe)
        print 'showing cam'
    if symbol == pyglet.window.key.S:
        unsched()
        pyglet.clock.schedule_interval(saveframe, frameinterval)
        print 'saving ghosts'
    elif symbol == pyglet.window.key.ESCAPE:
        print 'terminating processes',
        unsched()
        pool.close()
        pool.join()
        cam.release()
        pyglet.app.exit()

pyglet.clock.schedule(display)
pyglet.clock.schedule(showframe)
pyglet.app.run()
