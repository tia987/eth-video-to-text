# Video Transcriber GUI Application

A Python GUI application that transcribes audio from online videos using OpenAI's Whisper AI, built with PyQt6.

## Features

- Download videos from direct URLs
- Extract audio using FFmpeg
- Transcribe audio using Whisper AI models
- Multiple model sizes for different needs (tiny, base, small, medium, large, turbo). Set up accordingly to Whisper AI models.

## Prerequisites

- Python 3.10
- FFmpeg installed system-wide

## Installation

1. **Install FFmpeg** (if not already installed):
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg

   # MacOS (using Homebrew)
   brew install ffmpeg

   # Windows (using chocolatey)
   choco install ffmpeg
2. **Install pip3 packages**
    just run ```bash installation.sh``` to install all the necessary packages


## Run the application:
```bash
source vtt/bin/activate
python3 main.py
```

## Limitations

- Requires direct video URLs (doesn't support streaming platforms)
- Transcription speed depends on model size and hardware
- Large models require significant RAM (8GB+ recommended)
- Currently processes one video at a time

## TODOs
- --Add audio and video cache--
- RSS to eth websites
- cache from rss videos + selection of which videos to play
- Settings and advanced controls
- Text resize
- delete cache through GUI
- Change pitch when speeding video
- Increase video size
- if not transcribed, pop up small window asking if transcribe or not
- add missing time at the right of bar