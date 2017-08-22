#!/usr/bin/python
import wave
import pyaudio
from glob import glob

## TODO??? command line options
import hauntconfig as conf


class AudioPlayer:
    audio = None
    audiofile = ''
    waveform = None
    stream = None

    def __init__(self, audiofile):
        self.audio = pyaudio.PyAudio()
        self.audiofile = audiofile
        self.waveform = wave.open(self.audiofile, "rb")

    def reset_time(self, percent=0):
        self.waveform.setpos(
            long(.01*percent*self.waveform.getnframes()))
        print '{}%={}'.format(percent, float(self.waveform.tell())/self.waveform.getframerate())

    def get_time(self):
        return float(self.waveform.tell())/self.waveform.getframerate()

    def audio_callback(self, in_data, frame_count, time_info, status):
        if self.waveform.tell()>(self.waveform.getnframes()-frame_count):
            self.reset_time()
        data = self.waveform.readframes(frame_count)
        return (data, pyaudio.paContinue)

    def play(self):
        self.audio_stream = self.audio.open(
            format=self.audio.get_format_from_width(self.waveform.getsampwidth()),
            channels=self.waveform.getnchannels(),
            rate=self.waveform.getframerate(),
            output=True,
            stream_callback=self.audio_callback)
        self.audio_stream.start_stream()

    def close(self):
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
        if self.waveform:
            self.waveform.close()
            self.waveform = None
        if self.audio:
            self.audio.terminate()
            self.audio = None


class Syncher:
    frameglob = ''
    framerate = 1
    av_offset = 0.0
    frames = []
    numframes = 0
    audio_player = None

    def __init__(self, frameglob='tmp/*.png', framerate=conf.FRAMERATE,
                 audiofile = 'tmp/audio.wav', av_offset=conf.AV_OFFSET):
        self.frameglob = frameglob
        self.framerate = framerate
        self.av_offset = av_offset
        self.frames = sorted(glob(frameglob))
        self.numframes = len(self.frames)
        self.audio_player = AudioPlayer(audiofile)
        self.reset_time()

    def reset_time(self, percent=0):
        self.audio_player.reset_time(percent)

    def get_time(self):
        now = self.audio_player.get_time()+self.av_offset
        cam_cuesheet.tick(now)
        return now

    def get_frame(self):
        return self.frames[
            int(self.get_time()*self.framerate)%self.numframes]

    def play_audio(self):
        self.audio_player.play()

    def close(self):
        self.audio_player.close()


syncher = Syncher()

class CueSheet:

    def __init__(self, cuedict, callback):
        assert cuedict.has_key(0), "No cue for 0"
        self.current = None
        self.callback = callback
        self.cues = [(k, cuedict[k])
                     for k in sorted(cuedict.keys(), reverse=True)]

    def timestamp2cue(self, timestamp):
        for when, what in self.cues:
            if timestamp>=when:
                return what

    def range(self):
        return set([c[1] for c in self.cues])

    def trigger(self, cue):
        self.callback(cue)
        self.current = cue
        print "  trigger {}".format(cue)

    def tick(self, timestamp):
        cue = self.timestamp2cue(timestamp)
        if cue!=self.current:
            print "at {}:".format(timestamp)
            self.trigger(cue)

from subprocess import Popen
cam_cuesheet = CueSheet(
    conf.CAM_CUESHEET,
    lambda cfg: Popen("uvcdynctrl -L {}".format(cfg), shell=True))

baseframes = {}
def getbase():
    return baseframes.get(
        cam_cuesheet.current,
        # __default__ gets initialized later on (as failsafe)
        baseframes.get('__default__'))

import cv2
import numpy as np

def getimg():
    return cam.read()[1]

def saveghost(img, fnum):
    return cv2.imwrite("tmp/ghost%04i.png" % (fnum), img)

def loadghost(frame):
    return cv2.imread(frame)

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
    def updatebase(cam_profile):
        global baseframes
        baseframes[cam_profile] = np.zeros(img.shape)
        for i in range(basesize):
            baseframes[cam_profile] += 1.0 * getimg() / basesize
        baseframes[cam_profile] = slim(np.uint8(baseframes[cam_profile]))
    updatebase('__default__')  # against evil eye

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
    ghostresult = pool.apply_async(loadghost, (syncher.get_frame(),))
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
        ghostresult = pool.apply_async(loadghost, (syncher.get_frame(),))

    maskresult = pool.apply_async(getmask, (getbase(), slimimg))
    mask = maskresult.get()
    def updatemask():
        updateimg()
        global mask, maskresult, maskcnt
        if(False == maskresult.ready()): return
        mask = maskresult.get()
        maskresult = pool.apply_async(getmask, (getbase(), slimimg))
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
        if symbol >= pyglet.window.key._0 and \
           symbol <= pyglet.window.key._9:
           print "reset to {}%".format(10*(symbol-pyglet.window.key._0))
           syncher.reset_time(10*(symbol-pyglet.window.key._0))
        elif symbol == pyglet.window.key.SPACE:
            for i,profile in enumerate(cam_cuesheet.range()):
                pyglet.clock.schedule_once(
                    lambda *args, **kwargs:
                        cam_cuesheet.trigger(profile),
                    i+0.1)
                pyglet.clock.schedule_once(
                    lambda *args, **kwargs:
                        updatebase(profile),
                    i+1.0)
            pyglet.clock.schedule_once(
                lambda *args, **kwargs:
                        cam_cuesheet.tick(0),
                    len(cam_cuesheet.range()))
            cam_cuesheet.tick(0)  # reset
            print 'all base frames set.'
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

            syncher.reset_time()
            syncher.play_audio()
            print 'playing audio'
            pyglet.clock.schedule(blendframe)
            print 'showing ghosts'
        elif symbol in (pyglet.window.key.ESCAPE, pyglet.window.key.Q):
            print 'terminating processes',
            unsched()
            syncher.close()
            pool.close()
            pool.join()
            cam.release()
            pyglet.app.exit()

    pyglet.clock.schedule(display)
    pyglet.app.run()
