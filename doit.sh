#!/bin/sh
cd "$(dirname "$0")"
. venv/bin/activate
python haunt.py
echo -n 'press enter...'
head -1 - > /dev/null
