#!/bin/sh
mkdir tmp # wouldn't hurt ;)
rm tmp/*.png tmp/audio.wav
ffmpeg -i "$1" tmp/ghost%04d.png
ffmpeg -i "$1" tmp/audio.wav
