haunter
=======

We no longer save frames. we shoot a video (e.g. with guvcview) then
`./stripvid.sh somevid.mkv`

You also need to `cp hauntconfig-example.py hauntconfig.py` and edit.

To run: `./doit.sh`. See also `example.desktop` (for the ladies).

----

Computer vision tricks for a haunted house installation.

Currently consists of a single python script for experimentation. Parameters are hard coded.

Without change, the script will search for the first video capture device and start capturing, reporting the image size
once and the number of frames processed every second. Pressing the space bar will advance the script through the
following modes:

1. show - show live mirror
2. save - save frames for ghost video
3. show - show live mirror
4. setbase - set base image (auto advances after averaging 10 frames)
5. compare - show comparison of current frame to base image (for threshold fine-tuning)
6. ghost - blend live and ghost video)

Pressing arrow up and down will increase and decrease the threshold accordingly.

Pressing g will change grad function.

Pressing the shift key will start recording video to out.avi.

Other available functions (set with the funcs variable):
* donot - does nothing, for testing
* slim - show downsampled value map
* mask - show the blending mask
