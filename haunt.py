#!/usr/bin/python
#
# Experimentation script.
# Tubables are marked with triple hashes.
#
import cv2
import numpy as np
from time import time

###
camnum = 2
while True:
    print "Trying to access camera number %i" % (camnum)
    cam = cv2.VideoCapture(camnum)
    if cam.read()[0]: break
    if camnum < 0: raise Exception('No camera found')
    camnum -= 1

cam.set(3, 1280)
cam.set(4, 720)
_, img = cam.read()
height, width, depth = img.shape
print "Using camera %i with image %s" % (camnum, str(img.shape))

def donot(img):
    return False

def show(img):
    return img

fnum = -1
def record(img):
    global fnum
    fnum += 1
    cv2.imwrite("ghost%03i.png" % (fnum), img)
    return img

###
zoneheight, zonewidth = height, width / 2
def recordzone(img):
    return record(img[0:zoneheight, 0:zonewidth])

def slim(img):
    img = cv2.pyrDown(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, _, img = cv2.split(img)
    return img
base = slim(cam.read()[1])

###
basenumber = 10
def setbase(img):
    global base
    base = slim(img) / 10.0
    for i in range(basenumber):
        base = base + (slim(cam.read()[1]) / 10.0)
    base = np.uint8(base)
    step()
    return False

global th
###
th = 25
def compare(img):
    dif = cv2.absdiff(base, slim(img))
    _, dif = cv2.threshold(dif, th, 255, cv2.THRESH_BINARY)
    ker = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    dif = cv2.erode(dif, ker, iterations=3)
    dif = cv2.dilate(dif, ker, iterations=6)
    return dif

###
gpos = (zoneheight / 4, zonewidth / 4)
noise = 1
def ghost(img):
    global fnum, opac
    fnum += 1
    frame = cv2.imread("ghost%03i.png" % (fnum))
    if frame is None:
        fnum = -1
        return False

    opac = 1
    maxdist = zonewidth / 4
    mindist = maxdist
    contours, _ = cv2.findContours(compare(img), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) < noise: continue
        mindist = min(mindist, abs(cv2.pointPolygonTest(c, gpos, True)))
    opac = mindist / maxdist

    ghost = img.copy()
    ghost[0:zoneheight, 0:zonewidth] = frame
    img = cv2.addWeighted(img, 1 - opac, ghost, opac, 0)
    return img

def gradcont(img, contours):
    for i in range(1, 200, 20):
        cv2.drawContours(img, contours, -1, i, 80 - (i / 3))
    cv2.drawContours(img, contours, -1, 255, -1)

def gradrects(img, rects):
    rects = [np.int0(cv2.cv.BoxPoints(r)) for r in rects]
    for i in range(1, 255, 15):
        cv2.drawContours(img, rects, -1, i, 80 - (i / 3))
    cv2.drawContours(img, rects, -1, 255, -1)

def distance(p1, p2):
    x = p1[0] - p2[0]
    y = p1[1] - p2[1]
    return ((x ** 2) + (y ** 2)) ** .5

def grad(img):
    global fnum
    fnum += 1
    ghost = cv2.imread("ghost%03i.png" % (fnum))
    if ghost is None:
        fnum = -1
        return False

    dif = compare(img)
    contours, _ = cv2.findContours(dif.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.minAreaRect(c) for c in contours if cv2.contourArea(c) > noise]

    gradrects(dif, rects)
    dif = cv2.pyrUp(dif)
    dif = cv2.blur(dif, (10, 10))
    dif = dif / 255.0
    dif = cv2.merge((dif, dif, dif))
    img = np.uint8((img * dif) + ((1 - dif) * ghost))
    return img

###
funcs = [show, setbase, ghost]
funcs = [show, setbase, compare]
funcs = [show, recordzone, show, setbase, ghost]
funcs = [show, record, show, setbase, grad]
funcs = [show, setbase, grad]
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
    k = cv2.waitKey(1)
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
        elif 1113938 == k:
            th += 1
            print "Threshold raised to %i" %(th)
        elif 1113940 == k:
            th -= 1
            print "Threshold lowered to %i" %(th)
        else:
            print "unknown key %i" % (k)
