#!/bin/sh
mkdir tmp # wouldn't hurt ;)
rm tmp/*.png
ffmpeg -i "$1" tmp/ghost%04d.png
ffmpeg -i "$1" tmp/audio.mp3
