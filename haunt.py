#!/usr/bin/python
from glob import glob
import datetime

## TODO??? command line options
import hauntconfig as conf

class Syncher:
    frameglob = ''
    framerate = 1
    av_offset = 0
    frames = []
    numframes = 0
    reftime = None

    def __init__(self, frameglob='tmp/*.png',
        framerate=conf.FRAMERATE, av_offset=conf.AV_OFFSET):
        self.frameglob = frameglob
        self.framerate = framerate
        self.av_offset = av_offset
        self.frames = sorted(glob(frameglob))
        self.numframes = len(self.frames)
        self.reset_time()

    def reset_time(self):
        self.reftime = datetime.datetime.now()

    def get_time(self):
        return (datetime.datetime.now()-self.reftime).total_seconds()+self.av_offset

    def get_frame(self):
        return self.frames[int(self.get_time()*self.framerate)%self.numframes]

syncher = Syncher()

import cv2
import numpy as np

def getimg():
    return cam.read()[1]

def saveghost(img, fnum):
    return cv2.imwrite("tmp/ghost%04i.png" % (fnum), img)

def loadghost(syncher):
    return cv2.imread(syncher.get_frame())

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


from multiprocessing import freeze_support
if __name__ == '__main__':
    freeze_support()

    camnum = 2
    while True:
        print "trying to access camera number %i" % (camnum)
        cam = cv2.VideoCapture(camnum)
        if cam.read()[0]: break
        if camnum < 0: raise Exception('No camera found')
        camnum -= 1
    camwidth = conf.CAMWIDTH
    camheight = conf.CAMHEIGHT
    cam.set(3, camwidth)
    cam.set(4, camheight)
    img = getimg()
    shape = height, width, depth = img.shape
    print "using camera %i with image %s" % (camnum, str(shape))

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

    th = conf.THRESHOLD
    noise = conf.NOISE
    blur = conf.BLUR
    aurasize = conf.AURASIZE
    aurasteps = conf.AURASTEPS
    alphamin = 255 % aurasteps
    alphastep = 255 / aurasteps
    sizestep = aurasize / (aurasteps - 1)

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

    fnum = -1
    def updatesaveghost():
        global fnum
        fnum += 1
        pool.apply_async(saveghost, (img, fnum))
    ghostresult = pool.apply_async(loadghost, (syncher,))
    ghost = img
    def updateloadghost():
        global fnum, ghost, ghostresult, ghostcnt
        fnum += 1
        if(False == ghostresult.ready()): return
        result = ghostresult.get()
        if result is None:
            fnum = 0
        else:
            ghost = result
            ghostcnt += 1
        global syncher
        ghostresult = pool.apply_async(loadghost, (syncher,))

    maskresult = pool.apply_async(getmask, (base, slimimg))
    mask = maskresult.get()
    def updatemask():
        updateimg()
        global mask, maskresult, maskcnt
        if(False == maskresult.ready()): return
        mask = maskresult.get()
        maskresult = pool.apply_async(getmask, (base, slimimg))
        maskcnt += 1

    blendresult = pool.apply_async(getblend, (img, ghost, mask))
    blend = blendresult.get()
    def updateblend():
        updatemask()
        updateloadghost()
        global blend, blendresult, blendcnt
        if(False == blendresult.ready()): return
        blend = blendresult.get()
        blendresult = pool.apply_async(getblend, (img, ghost, mask))
        blendcnt += 1

    def showframe(_):
        updateimg()
        global out
        out = img

    def saveframe(_):
        showframe(_)
        updatesaveghost()

    def maskframe(_):
        updatemask()
        global out
        out[:,:,0] = mask
        out[:,:,1] = mask
        out[:,:,2] = mask

    def blendframe(_):
        updateblend()
        global out
        out = blend

    import pyglet
    window = pyglet.window.Window(resizable=True)
    from time import time
    stime = time()
    imgcnt = ghostcnt = maskcnt = blendcnt = 0
    out = img
    def display(_):
        global stime, imgcnt, ghostcnt, maskcnt, blendcnt
        ctime = time()
        if ctime - stime >= 1:
            print '%.2f fps (%i captures, %i ghosts, %i masks, %i blends)' % (
                pyglet.clock.get_fps(), imgcnt, ghostcnt, maskcnt, blendcnt
            )
            imgcnt = ghostcnt = maskcnt = blendcnt = 0
            stime = ctime

        window.clear()
        pyglet.image.ImageData(width, height, 'bgr', cv2.flip(out, 1).tostring(), -1 * depth * width).blit(0, 0)

    def unsched():
        pyglet.clock.unschedule(showframe)
        pyglet.clock.unschedule(saveframe)
        pyglet.clock.unschedule(maskframe)
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
            print 'display cam'
        elif symbol == pyglet.window.key.S:
            unsched()
            pyglet.clock.schedule(saveframe)
            print 'saving ghosts'
        elif symbol == pyglet.window.key.M:
            unsched()
            pyglet.clock.schedule(maskframe)
            print 'showing mask'
        elif symbol == pyglet.window.key.G:
            unsched()

            ###@@@ this didn't work :(
            #OBTW requires https://avbin.github.io
            #pyglet.options['audio'] = ('openal',) # or something
            #player = pyglet.media.load('tmp/audio.mp3').play()
            #...

            ###@@@ this works, but meh
            import subprocess
            subprocess.Popen('killall mpg123',shell=True)
            subprocess.Popen('mpg123 tmp/audio.mp3',shell=True)

            syncher.reset_time()
            pyglet.clock.schedule(blendframe)
            print 'showing ghosts'
        elif symbol in (pyglet.window.key.ESCAPE, pyglet.window.key.Q):
            print 'terminating processes',
            unsched()
            pool.close()
            pool.join()
            cam.release()
            pyglet.app.exit()

    pyglet.clock.schedule(display)
    pyglet.app.run()
