import os
import subprocess
import sys

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, 
                             QFileDialog, QHBoxLayout, QSlider)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, QTimer, Qt
from PyQt6.QtGui import QTextCursor

from cache_handler import *

import whisper
import threading
import requests
import ffmpeg
import json

def download_video(url, output_path):
    """Downloads video using requests instead of wget."""
    response = requests.get(url, stream=True)
    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

def extract_audio(video_path, audio_path):
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, format='mp3', acodec='libmp3lame', audio_bitrate='192k')
            .run(overwrite_output=True)
        )
        print(f"Audio extracted successfully: {audio_path}")
    except ffmpeg.Error as e:
        print(f"Error: {e.stderr.decode()}")

def transcribe_audio(audio_path, model_name):
    """Check cache before running Whisper AI and save transcription if not cached."""
    cache_file = get_cache_path(audio_path, model_name)
    
    # Check if cached transcription exists
    if os.path.exists(cache_file):
        print(f"Loading cached transcription: {cache_file}")
        with open(cache_file, "r") as f:
            return json.load(f)  # Load cached transcription

    print("Running Whisper AI...")
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)

    # Save the result in cache
    with open(cache_file, "w") as f:
        json.dump(result, f)

    return result


class VideoTranscriber(QWidget):
    def __init__(self):
        super().__init__()
        self.UI()
    
    def UI(self):
        horizontal_layout_1 = QHBoxLayout()
        vertical_layout_1 = QVBoxLayout()
        vertical_layout_2 = QVBoxLayout()
        horizontal_layout_2 = QHBoxLayout()
        
        # Left Section (Video Player Section)
        self.video_widget = QVideoWidget()
        horizontal_layout_1.addLayout(vertical_layout_2, 2)
        vertical_layout_2.addWidget(self.video_widget)
        vertical_layout_2.addLayout(horizontal_layout_2)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)

        # Right Section (Controls + Transcript)
        self.label = QLabel("Enter Video URL or PATH:")
        vertical_layout_1.addWidget(self.label)
        
        self.url_entry = QLineEdit()
        vertical_layout_1.addWidget(self.url_entry)
        
        self.transcribe_button = QPushButton("Start Transcription")
        self.transcribe_button.clicked.connect(self.start_transcription)
        vertical_layout_1.addWidget(self.transcribe_button)

        # Add file selection button
        self.select_file_button = QPushButton("Select Video File")
        self.select_file_button.clicked.connect(self.select_video_file)
        vertical_layout_1.addWidget(self.select_file_button)
        
        # Forward, pause and Backward buttons
        self.backward_button = QPushButton("⏪")
        self.backward_button.clicked.connect(self.backward_10s)
        horizontal_layout_2.addWidget(self.backward_button, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.playback_button = QPushButton("⏯")
        self.playback_button.clicked.connect(self.toggle_playback)
        horizontal_layout_2.addWidget(self.playback_button, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.forward_button = QPushButton("⏩")
        self.forward_button.clicked.connect(self.forward_10s)
        horizontal_layout_2.addWidget(self.forward_button, 0, Qt.AlignmentFlag.AlignLeft)

        # Slider for video position
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setRange(0, 100)
        self.position_slider.sliderMoved.connect(self.set_position)
        horizontal_layout_2.addWidget(self.position_slider, 1)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        vertical_layout_1.addWidget(self.output_text)

        self.combo_box = QComboBox()
        self.combo_box.addItems(["tiny", "base", "small", "medium", "large", "turbo"])
        vertical_layout_1.addWidget(self.combo_box)

        horizontal_layout_1.addLayout(vertical_layout_1, 1)
        self.setLayout(horizontal_layout_1)
        self.setWindowTitle("Video Transcriber")
        self.resize(900, 600)

        # Update slider with video progress
        self.media_player.positionChanged.connect(self.update_transcription)
        self.media_player.positionChanged.connect(self.update_slider)
        self.media_player.durationChanged.connect(self.set_slider_range)
    
    def start_transcription(self):
        url = self.url_entry.text()
        if not url:
            self.output_text.setText("Please enter a video URL.")
            return
        
        # threading.Thread(target=process_video, args=(url, self.output_text), daemon=True).start()
        selected_model = self.combo_box.currentText()
        self.process_video(url, selected_model)

    def select_video_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)")
        if file_path:
            self.url_entry.setText(file_path)

    def process_video(self, url_or_path, model_name):
        try:
            video_path = "downloaded_video.mp4" if url_or_path.startswith("http") else url_or_path
            audio_path = "audio.wav" # TODO: make this different
            
            if url_or_path.startswith("http"):
                self.output_text.setText("Downloading video...")
                download_video(url_or_path, video_path)
            
            self.output_text.setText("Extracting audio...")
            extract_audio(video_path, audio_path)
            
            self.output_text.setText("Transcribing audio...")
            transcript = transcribe_audio(audio_path, model_name)
            
            self.output_text.setText("")
            # self.transcription_words = transcript["text"]#.split()
            self.transcription_segments = transcript["segments"]
            self.current_index = 0
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()
            self.update_transcription()
        except Exception as e:
            self.output_text.setText(f"Error: {str(e)}")

    def update_transcription(self, position):
        current_time = position / 1000  # Convert ms to seconds
        previous_text = []
        upcoming_text = []
        previous_lines = []
        upcoming_lines = []
        active_word = ""

        for segment in self.transcription_segments:
            if segment['start'] < current_time:
                previous_lines.append(segment['text'])
            elif segment['start'] <= current_time <= segment['end']:
                active_segment = segment['text']
            else:
                upcoming_lines.append(segment['text'])

        for segment in self.transcription_segments:
            if segment['start'] <= current_time <= segment['end']:
                words = segment['text'].split()  # Split segment into words
                elapsed_time = current_time - segment['start']
                segment_duration = segment['end'] - segment['start']
                
                # Find which word should be highlighted based on elapsed time
                word_index = int((elapsed_time / segment_duration) * len(words))
                word_index = min(word_index, len(words) - 1)  # Ensure index is in range
                
                previous_text = words[:word_index]
                previous_text.append(' ')
                active_word = words[word_index]
                active_word += " "
                upcoming_text = words[word_index + 1:]
                break
            elif segment['start'] < current_time:
                previous_text.append(segment['text'])
            else:
                upcoming_text.append(segment['text'])

        # Preserve scroll position
        scroll_position = self.output_text.verticalScrollBar().value()

        # Format the text with word-level highlighting
        transcript_html = (
            # f"<div style='text-align: center;'>"
            f"<span style='color: white;'>{' '.join(previous_lines[-7:])}</span>"  # Show last 10 lines
            f"<span style='color: white;'>{' '.join(previous_text[-20:])}</span>"  # Last 10 spoken words
            f"<span style='color: cyan; font-weight: bold;'>{active_word}</span>"
            f"<span style='color: gray;'>{' '.join(upcoming_text[:20])}</span>"  # Next 10 words
            f"<span style='color: gray;'>{' '.join(upcoming_lines[:7])}</span>"  # Show next 10 lines
            # f"</div>"
        )

        self.output_text.setHtml(transcript_html)

        # Restore scroll position
        self.output_text.verticalScrollBar().setValue(scroll_position)

    # Functions for video playing
    def forward_10s(self):
        self.media_player.setPosition(self.media_player.position() + 10000)
    
    def backward_10s(self):
        self.media_player.setPosition(self.media_player.position() - 10000)
    
    def set_position(self, position):
        self.media_player.setPosition(position)
    
    def update_slider(self, position):
        self.position_slider.setValue(position)
    
    def set_slider_range(self, duration):
        self.position_slider.setRange(0, duration)

    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoTranscriber()
    window.show()
    sys.exit(app.exec())