import os
import subprocess
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox
import whisper
import threading
import requests
import ffmpeg

# def download_video(url, output_path):
#     """Downloads video from a URL using wget."""
#     command = ["wget", "-O", output_path, url]
#     subprocess.run(command, check=True)
def download_video(url, output_path):
    """Downloads video using requests instead of wget."""
    response = requests.get(url, stream=True)
    with open(output_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

# def extract_audio(video_path, audio_path):
#     """Extracts audio from video using FFmpeg."""
#     command = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path]
#     subprocess.run(command, check=True)
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
    """Transcribes the audio using Whisper AI."""
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)

    return result["text"]

def process_video(url, output_widget, model_name):
    try:
        video_path = "downloaded_video.mp4"
        audio_path = "audio.wav"
        
        output_widget.setText("Downloading video...")
        download_video(url, video_path)
        
        output_widget.setText("Extracting audio...")
        extract_audio(video_path, audio_path)
        
        output_widget.setText("Transcribing audio...")
        transcript = transcribe_audio(audio_path, model_name)
        
        output_widget.setText(transcript)
    except Exception as e:
        output_widget.setText(f"Error: {str(e)}")

class VideoTranscriber(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("Enter Video URL:")
        layout.addWidget(self.label)
        
        self.url_entry = QLineEdit()
        layout.addWidget(self.url_entry)
        
        self.transcribe_button = QPushButton("Start Transcription")
        self.transcribe_button.clicked.connect(self.start_transcription)
        layout.addWidget(self.transcribe_button)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.combo_box = QComboBox()
        self.combo_box.addItems(["tiny", "base", "small", "medium", "large", "turbo"])
        layout.addWidget(self.combo_box)
        
        self.setLayout(layout)
        self.setWindowTitle("Video Transcriber")
        self.resize(600, 400)
    
    def start_transcription(self):
        url = self.url_entry.text()
        if not url:
            self.output_text.setText("Please enter a video URL.")
            return
        
        # threading.Thread(target=process_video, args=(url, self.output_text), daemon=True).start()
        selected_model = self.combo_box.currentText()
        process_video(url, self.output_text, selected_model)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoTranscriber()
    window.show()
    sys.exit(app.exec())