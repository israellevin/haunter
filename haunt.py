#!/usr/bin/python
#
# Experimentation script.
# Tubables are marked with triple hashes.
#
import cv2
import numpy as np
from time import time

###
hd=False

if hd:
    cam = cv2.VideoCapture(1)
    cam.set(3, 1280)
    cam.set(4, 720)
else:
    cam = cv2.VideoCapture(-1)

_, img = cam.read()
height, width, depth = img.shape
print "Got image %s" % (str(img.shape))

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

gpos = (zoneheight / 4, zonewidth / 4)
def slim(img):
    img = cv2.pyrDown(img)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    _, _, img = cv2.split(img)
    return img

###
noise = 1
bgs = cv2.BackgroundSubtractorMOG()
def ghost(img):
    global fnum, bgs, opac

    fnum += 1
    frame = cv2.imread("ghost%03i.png" % (fnum))
    if frame is None:
        fnum = -1
        return
    ghost = img.copy()
    ghost[0:zoneheight, 0:zonewidth] = frame

    dif = bgs.apply(slim(img))
    ker = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    dif = cv2.erode(dif, ker, iterations=2)
    dif = cv2.dilate(dif, ker, iterations=2)

    opac = 1
    maxdist = zonewidth / 4.0
    mindist = maxdist
    contours, _ = cv2.findContours(dif.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) < noise: continue
        mindist = min(mindist, abs(cv2.pointPolygonTest(c, gpos, True)))
    opac = mindist / maxdist

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

###
th = 25
def grad(img):
    global fnum

    fnum += 1
    ghost = cv2.imread("ghost%03i.png" % (fnum))
    if ghost is None:
        fnum = -1
        return False

    dif = cv2.absdiff(base, slim(img))
    _, dif = cv2.threshold(dif, th, 255, cv2.THRESH_BINARY)
    ker = cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3))
    dif = cv2.erode(dif, ker, iterations=3)
    dif = cv2.dilate(dif, ker, iterations=6)

    contours, _ = cv2.findContours(dif.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = [cv2.minAreaRect(c) for c in contours if cv2.contourArea(c) > noise]

    gradrects(dif, rects)
    dif = cv2.pyrUp(dif)
    dif = cv2.blur(dif, (10, 10))
    dif = dif / 255.0
    dif = cv2.merge((dif, dif, dif))
    img = np.uint8((img * dif) + ((1 - dif) * ghost))
    return img

def setbase(img):
    global bgs, base
    bgs = cv2.BackgroundSubtractorMOG()
    base = slim(img)
    step()
    return base

###
funcs = [show, recordzone, show, setbase, ghost]
funcs = [show, setbase, ghost]
funcs = [show, setbase, grad]
funcs = [show, record, show, setbase, grad]
def step():
    global funcs
    funcs.append(funcs.pop(0))
    print "moving to %s" % (funcs[0])

###
framecnt = 0
cv2.namedWindow('out', 1)
recorder = False
stime = time()
while True:
    _, img = cam.read()
    img = cv2.flip(img, 1)
    img = funcs[0](img)
    if not img is False:
        cv2.imshow('out', img)
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
                global recorder
                recorder = cv2.VideoWriter('out.avi', cv2.cv.FOURCC('M', 'J', 'P', 'G'), 25, (width, height))
                print 'starting to record'
            else:
                print 'already recording'
        else:
            print "unknown key %i" % (k)
