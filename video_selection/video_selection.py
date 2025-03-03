import os, json, ffmpeg, whisper
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QDialog, QLineEdit,
    QLabel, QCheckBox, QFileDialog, QHBoxLayout
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QUrl

from cache_handler import *
from video_downloader import *

class AddVideoDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Save video")
        self.init_ui()
        self.video_path_cache = ""
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout_horizontal = QHBoxLayout()
        
        # URL input
        self.url_entry = QLineEdit()
        self.url_entry.setPlaceholderText("Enter video URL or local path")
        layout_horizontal.addWidget(QLabel("Video URL/Path:"))
        layout_horizontal.addWidget(self.url_entry)
        
        layout_horizontal.addWidget(QLabel(" or"))
        
        # File selection button
        self.file_button = QPushButton("Select Video File")
        self.file_button.clicked.connect(self.select_video_file)
        layout_horizontal.addWidget(self.file_button)
        
        layout.addLayout(layout_horizontal)
        
        # Additional box for video name (only visible for local paths)
        self.name_label = QLabel("Video Name:")
        self.name_entry = QLineEdit()
        self.name_label.hide()
        self.name_entry.hide()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_entry)
        
        # Checkbox for immediate transcription
        self.transcribe_checkbox = QCheckBox("Transcribe Immediately")
        self.transcribe_checkbox.setChecked(True)
        layout.addWidget(self.transcribe_checkbox)
        
        # Confirm button - calls our custom on_confirm method
        self.confirm_button = QPushButton("Save Video")
        self.confirm_button.clicked.connect(self.on_confirm)
        layout.addWidget(self.confirm_button)
        
        self.setLayout(layout)
        
        # When the URL entry changes, check whether to show the video name fields.
        self.url_entry.textChanged.connect(self.check_url_input)
        
    def select_video_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Select Video File", "", "Video Files (*.mp4 *.avi *.mov)"
        )
        if file_path:
            self.url_entry.setText(file_path)
    
    def check_url_input(self, text):
        # If text is non-empty and doesn't start with 'http', assume it's a local file path.
        if text:
            self.name_label.show()
            self.name_entry.show()
        else:
            self.name_label.hide()
            self.name_entry.hide()
    
    def get_video_data(self):
        # video_path = self.video_path_cache
        video_path = self.url_entry.text()
        transcribe_now = self.transcribe_checkbox.isChecked()
        video_name = self.name_entry.text() if self.name_entry.isVisible() else None
        return video_path, transcribe_now, video_name
    
    def on_confirm(self):
        video_path, transcribe_now, video_name = self.get_video_data()
        if video_path:
            if transcribe_now:
                # Use the provided video name if available; otherwise use a default.
                if not video_name or video_name.strip() == "":
                    video_name = "downloaded_video.mp4"
                self.process_video(video_path, 'tiny', video_name)
        self.accept()
    
    def process_video(self, url_or_path, model_name, video_name="downloaded_video.mp4"):
        # Add .mp4 if video_name doesn't have it
        if video_name != "":
            if not video_name.lower().endswith(".mp4"):
                video_name += ".mp4"

        # Use video_name if downloading from a URL; otherwise, use the local file path.
        video_path = "cache/videos/"+video_name if url_or_path.startswith("http") else url_or_path
        print("Video path to be processed:", video_path)
        audio_path = "cache/audios/audio.wav"
        self.video_path_cache = video_path

        if url_or_path.startswith("http"):
            # Check if the file already exists before downloading.
            if not os.path.exists(video_path):
                print("Downloading video...")
                download_video(url_or_path, video_path)
            else:
                print("Video already downloaded, skipping download.")

        cache_file = get_cache_path(video_path, model_name)
        if os.path.exists(cache_file):
            print(f"Loading cached transcription: {cache_file}")
            with open(cache_file, "r") as f:
                transcript = json.load(f)
        else:
            print("Extracting audio...")
            self.extract_audio(video_path, audio_path)
            print("Transcribing audio...")
            transcript = self.transcribe_audio(audio_path, video_path, model_name)
        print("Transcription complete!")
    
    @staticmethod
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
            print(f"Error extracting audio: {e.stderr.decode()}")
    
    @staticmethod
    def transcribe_audio(audio_path, video_path, model_name):
        cache_file = get_cache_path(video_path, model_name)
        print("Running Whisper AI...")
        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path)
        with open(cache_file, "w") as f:
            json.dump(result, f)
        return result

# --- Lecture Selection Interface --- #
class VideoSelectionWidget(QWidget):
    def __init__(self, switch_to_transcriber_callback):
        super().__init__()
        self.switch_to_transcriber_callback = switch_to_transcriber_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.video_list = QListWidget()
        # Populate with example lecture entries (you can replace these with real metadata)
        self.video_list.addItem("Lecture 1: Introduction")
        self.video_list.addItem("Lecture 2: Advanced Topics")
        self.video_list.addItem("Lecture 3: Transcription Demo")
        layout.addWidget(self.video_list)
        
        open_button = QPushButton("Open Selected Lecture")
        open_button.clicked.connect(self.open_video)
        layout.addWidget(open_button)

        add_video_button = QPushButton("Save Video")
        add_video_button.clicked.connect(self.open_add_video_dialog)
        layout.addWidget(add_video_button)
        
        self.setLayout(layout)
        self.setWindowTitle("Lecture Videos")
    
    def open_video(self):
        current_item = self.video_list.currentItem()
        if current_item:
            video_identifier = current_item.text()
            # In practice, use this identifier to look up the correct video URL/path.
            self.switch_to_transcriber_callback(video_identifier)

    def open_add_video_dialog(self):
        dialog = AddVideoDialog()
        if dialog.exec():
            video_path, transcribe_now, _ = dialog.get_video_data()
            if video_path:
                self.video_list.addItem(video_path)  # Add to the list
                if transcribe_now:
                    self.switch_to_transcriber_callback(video_path)