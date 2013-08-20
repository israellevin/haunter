#!/usr/bin/python
#
# Experimentation script.
#
# Tubables are marked with triple hashes.
import cv2
import numpy as np
from time import time

###
camwidth = 640
camheight = 480
camnum = 2
while True:
    print "Trying to access camera number %i" % (camnum)
    cam = cv2.VideoCapture(camnum)
    if cam.read()[0]: break
    if camnum < 0: raise Exception('No camera found')
    camnum -= 1

cam.set(3, camwidth)
cam.set(4, camheight)
_, img = cam.read()
height, width, depth = img.shape
print "Using camera %i with image %s" % (camnum, str(img.shape))

def donot(img):
    return False

def show(img):
    return img

fnum = -1
def save(img):
    global fnum
    fnum += 1
    cv2.imwrite("ghost%03i.png" % (fnum), img)
    return img

###
downsample = 1
def slim(img):
    for i in range(downsample):
        img = cv2.pyrDown(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, _, img = cv2.split(img)
    return img

###
basesize = 10
def setbase(img):
    global base
    base = 1.0 * slim(img) / basesize
    for i in range(basesize - 1):
        base += 1.0 * slim(cam.read()[1]) / basesize
    base = np.uint8(base)
    step()
    return False

###
th = 25
erodes = 6
dilates = 6
def compare(img):
    dif = cv2.absdiff(base, slim(img))
    _, dif = cv2.threshold(dif, th, 255, cv2.THRESH_BINARY)
    ker = cv2.getStructuringElement(cv2.MORPH_CROSS,(5,5))
    dif = cv2.erode(dif, ker, iterations=erodes)
    dif = cv2.dilate(dif, ker, iterations=dilates)
    return dif

###
aurasize = 100
aurastep = 20
aurafact = 255.0 / aurasize
def gradcont(img, contours):
    for i in range(1, 255, aurastep):
        cv2.drawContours(img, contours, -1, i, int((255 - i) / aurafact))
    cv2.drawContours(img, contours, -1, 255, -1)
    for i in range(downsample):
        img = cv2.pyrUp(img)
    img = cv2.blur(img, (10, 10))
    return img

def gradrects(img, contours):
    rects = [cv2.minAreaRect(c) for c in contours if cv2.contourArea(c) > noise]
    rects = [np.int0(cv2.cv.BoxPoints(r)) for r in rects]
    return gradcont(img, rects)

#FIXME ugly
def gradellipses(img, contours):
    ellipses = [cv2.fitEllipse(c) for c in contours if cv2.contourArea(c) > noise]

    for i in range(1, 255, aurastep):
        for e in ellipses:
            cv2.ellipse(img, e, i, int((255 - i) / aurafact))
    for e in ellipses:
        cv2.ellipse(img, e, 255, -1)
    for i in range(downsample):
        img = cv2.pyrUp(img)
    img = cv2.blur(img, (10, 10))
    return img

###
noise = 25
gradfuncs = [gradcont, gradrects, gradellipses]
def mask(img):
    dif = compare(img)
    contours, _ = cv2.findContours(dif.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    dif = gradfuncs[0](dif, contours)
    return dif

def ghost(img):
    global fnum
    fnum += 1
    ghost = cv2.imread("ghost%03i.png" % (fnum))
    if ghost is None:
        fnum = -1
        return False

    dif = mask(img)
    dif = dif / 255.0
    dif = cv2.merge((dif, dif, dif))
    img = np.uint8((img * dif) + ((1 - dif) * ghost))
    return img

###
funcs = [show, setbase, compare, mask]
funcs = [show, setbase, ghost]
funcs = [show, save, show, setbase, compare, ghost]
def step():
    global funcs
    funcs.append(funcs.pop(0))
    print "moving to %s" % (funcs[0])

###
framecnt = 0
cv2.namedWindow('out', 1)
global recorder
recorder = False
stime = time()
base = img
while True:
    _, img = cam.read()
    img = funcs[0](img)
    if not img is False:
        cv2.imshow('out', cv2.flip(img, 1))
        if(not recorder is False):
            recorder.write(img)

    # FPS calc
    if framecnt > -1:
        framecnt = framecnt + 1
        ctime = time()
        if ctime - stime >= 1:
            print '%i fps' % (framecnt)
            framecnt = 0
            stime = ctime

    # Keyboard
    k = cv2.waitKey(30)
    if -1 != k:
        if 27 == k or 1048603 == k:
            break
        elif 32 == k or 1048608 == k:
            step()
        elif 1114081 == k or 1114082 == k:
            if recorder is False:
                recorder = cv2.VideoWriter('out.avi', cv2.cv.FOURCC('M', 'J', 'P', 'G'), 25, (width, height))
                print 'starting to record'
            else:
                print 'already recording'
        elif 65362 == k:
            th += 1
            print "Threshold raised to %i" %(th)
        elif 65364 == k:
            th -= 1
            print "Threshold lowered to %i" %(th)
        elif 103 == k:
            global gradfuncs
            gradfuncs.append(gradfuncs.pop(0))
            print "moving to %s" % (gradfuncs[0])
        else:
            print "unknown key %i" % (k)
