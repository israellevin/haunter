#!/usr/bin/python
import os
import wave
import pyaudio
from glob import glob

import hauntconfig as conf

def beep():
    os.popen4('play beep.wav')

class AudioPlayer:
    audio = None
    audiofile = ''
    waveform = None
    audio_stream = None

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

    def stop(self):
        if self.audio_stream:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None

    def close(self):
        self.stop()
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
        light_cuesheet.tick(now)
        cam_cuesheet.tick(now)
        ghost_cuesheet.tick(now)
        return now

    def get_frame(self):
        return self.frames[
            int(self.get_time()*self.framerate)%self.numframes]

    def play_audio(self):
        self.audio_player.play()

    def stop(self):
        self.audio_player.stop()

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
    lambda arg: Popen("uvcdynctrl -L {}".format(arg), shell=True))

import requests
def get_url(u):
    try:
        return requests.get(u, allow_redirects=False)
    except:
        return None

from serial import Serial
from serial.tools.list_ports import comports

serial_switch = None
serialports = [
    # Only duinos
    (c.device, c.description) for c in comports() if c.description.find('dui')>=0]
if serialports:
    print "`duino device(s): {}".format(serialports)
    serial_switch = Serial(serialports[0][0])


def do_switch(u):
    if serial_switch: # prefer serial
        serial_switch.write(u[-1])
    else: # try wifi instead
        get_url(u)

light_cuesheet = CueSheet(conf.LIGHT_CUESHEET, do_switch)

ghost_cuesheet = CueSheet(conf.GHOST_CUESHEET, lambda x: None)

baseframes = {}
def getbase():
    return baseframes.get(
        (cam_cuesheet.current, light_cuesheet.current),
        # __default__ gets initialized later on (as failsafe)
        baseframes.get('__default__'))

def reset_cuesheets():
    cam_cuesheet.tick(0)
    light_cuesheet.tick(0)
    beep()

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
    def updatebase(state):
        global baseframes
        baseframes[state] = np.zeros(img.shape)
        for i in range(basesize):
            baseframes[state] += 1.0 * getimg() / basesize
        baseframes[state] = slim(np.uint8(baseframes[state]))
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
        if ghost_cuesheet.current=='blend':
            out = blend
        else:
            out = ghost

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
        syncher.stop()
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
            unsched()
            pyglet.clock.schedule(showframe)
            ncams = len(cam_cuesheet.range())
            nlights = len(light_cuesheet.range())
            for i, cam_state in enumerate(cam_cuesheet.range()):
                pyglet.clock.schedule_once(
                    lambda _, cs = cam_state:
                        cam_cuesheet.trigger(cs),
                    2*(nlights*i+0.1))
                for j, light_state in enumerate(light_cuesheet.range()):
                    pyglet.clock.schedule_once(
                        lambda _, ls=light_state:
                            light_cuesheet.trigger(ls),
                        2*(nlights*i+j+0.5))
                    pyglet.clock.schedule_once(
                        lambda _, cs=cam_state, ls=light_state:
                            updatebase((cs, ls)),
                        2*(nlights*i+j+0.9))
            pyglet.clock.schedule_once(
                lambda _:
                        reset_cuesheets(),
                        2*(nlights*ncams+1))
            # reset cam and light
            cam_cuesheet.tick(0) 
            light_cuesheet.tick(0)
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
            beep()
            pyglet.app.exit()

    pyglet.clock.schedule(display)
    pyglet.app.run()
