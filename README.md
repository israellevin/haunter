## Haunter

Computer vision tricks for a "haunted house" installation.

A preset source video gets blended with live camera
(shooting the same background) only where the image
differs from the base frame. This makes people in
the frame "ghost out" the people in the source video.

### Configuration

`cp hauntconfig-example.py hauntconfig.py` and edit.

### Preprocessing (source video/audio)

* Shoot a video (e.g. with guvcview)
* `./stripvid.sh YOURVIDEO.mkv`

### Running

Run `./doit.sh` (see also `example.desktop` [for the ladies]).

Keyboard commands:

* `f`: Toggle full screen.
* `space` (while scene is empty): Capture baseframe for all possible
  cam profiles with/without light (see WiFiSwitch). Beeps when done.
* `g`: Start "ghosting" (blending source video with cam).
       Pressing up/down arrows will increase and decrease the
       threshold accordingly.
* `0`,`1`,...,`9`: Jump to 0%,10%,...,90% of source video timeline.
* `m`: View the blending mask.
* `d`: Display cam image.
* `q`: Quit.

### WifiSwitch

Hardware (see the `Arduino` folder) that switches
an AC socket on/off (used for lighting).
`LIGHT_CUESHEET` at `hauntconfig.py` controls the timing.

Note: if arduino is connected via serial (9600 bd), you can
send it '1' to turn switch on, and '0' [or anything else] to turn it off.
`haunt.py` prefers serial over wifi (faster response, no setup hassle).
You can use `serial.sh` in order to test the switch manually
(1[+enter] to select the port, then type 1 or 0 to control the switch).

![WiFiSwitch](https://github.com/israellevin/haunter/raw/production/Arduino/WiFiSwitch.jpg)
