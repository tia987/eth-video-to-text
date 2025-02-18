#!/bin/bash

# Install FFMPEG if necessary
if command -v ffmpeg &>/dev/null; then
    echo "FFmpeg is installed."
else
    echo "Error: FFmpeg is not installed." >&2
    exit 1
fi

# Install required packages
python3.10 -m venv vtt
source vtt/bin/activate
pip3 install -r requirements.txt