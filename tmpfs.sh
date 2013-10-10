#!/bin/sh
if [ "$1" ]; then
    umount tmp && rmdir tmp
else
    mkdir tmp && mount -t tmpfs -o size=60% none tmp
fi
