haunter
=======

Computer vision tricks for a haunted house installation.

Currently consists of a single python script for experimentation. Parameters are hard coded.

Without change, the script will search for the first video capture device and start capturing, reporting the image size
once and the number of frames processed every second. Pressing the space bar will advance the script through the
following modes in a loop.

1. Show live mirror
2. Record frames for ghost video
3. Show live mirror
4. Set base image (auto advances after a single frame)
5. Haunting

Pressing the shift key will start recording video to out.avi.

Arrow up and down will increase and decrease the threshold.
