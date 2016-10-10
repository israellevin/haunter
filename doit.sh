#!/bin/sh
cd "$(dirname "$0")"
python haunt.py
echo -n 'press enter...'
head -1 - > /dev/null
