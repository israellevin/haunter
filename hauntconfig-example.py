CAMWIDTH = 1920
CAMHEIGHT = 1080
FRAMERATE = 24
AV_OFFSET = 0.5 # Seconds. Positive: video is delayed

THRESHOLD = 23
NOISE = 50
BLUR = 10
AURASIZE = 80
AURASTEPS = 4

CAM_CUESHEET = {
    0: "default.gpfl",
    10: "color.gpfl",
    20: "default.gpfl",
#    25: "grey.gpfl",
#    30: "default.gpfl"
}

LIGHT_ON = "http://192.168.1.132/arduino/digital/1"
LIGHT_OFF = "http://192.168.1.132/arduino/digital/0"

LIGHT_CUESHEET = {
    0: LIGHT_OFF,
    15: LIGHT_ON,
    28: LIGHT_OFF
}

GHOST_CUESHEET = {
    0: 'blend',
   20: 'source',
   23: 'blend'
}

### osd doesn't work in full screen mode :(
#CAPTION_CMD = 'aosd_cat -p 1 -x 0 -y 0 -e 1 -R "#ffefaf" -n "Alef Bold 32" -f 100 -o 100'
