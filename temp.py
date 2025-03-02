import sys, os, json, requests, threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QStackedWidget, QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout, QLineEdit, QTextEdit, QComboBox, QSlider, QFileDialog
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import ffmpeg
import whisper
from cache_handler import get_cache_path  # Make sure you have this module

# --- Utility functions for downloading and processing videos --- #
def download_video(url, output_path):
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

def transcribe_audio(audio_path, video_path, model_name):
    cache_file = get_cache_path(video_path, model_name)
    print("Running Whisper AI...")
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)
    with open(cache_file, "w") as f:
        json.dump(result, f)
    return result

# --- Video Transcriber Interface --- #
class VideoTranscriber(QWidget):
    def __init__(self, video_identifier, switch_back_callback):
        super().__init__()
        self.video_identifier = video_identifier  # Could be a URL, file path, or lecture title
        self.switch_back_callback = switch_back_callback
        self.transcription_segments = []
        self.current_index = 0
        self.init_ui()
    
    def init_ui(self):
        horizontal_layout_1 = QHBoxLayout()
        vertical_layout_1 = QVBoxLayout()
        vertical_layout_2 = QVBoxLayout()
        horizontal_layout_2 = QHBoxLayout()
        horizontal_layout_3 = QHBoxLayout()
        
        # Back button to return to the main selection view
        self.back_button = QPushButton("← Back to Lecture Selection")
        self.back_button.clicked.connect(self.switch_back_callback)
        vertical_layout_1.addWidget(self.back_button)
        
        # Left Section: Video Player
        self.video_widget = QVideoWidget()
        vertical_layout_2.addWidget(self.video_widget)
        vertical_layout_2.addLayout(horizontal_layout_2)
        horizontal_layout_1.addLayout(vertical_layout_2, 2)
        
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Right Section: Controls & Transcription
        self.label = QLabel("Enter Video URL or PATH:")
        vertical_layout_1.addWidget(self.label)
        self.url_entry = QLineEdit(self.video_identifier)  # Pre-fill with the identifier if applicable
        vertical_layout_1.addWidget(self.url_entry)
        self.transcribe_button = QPushButton("Start Transcription")
        self.transcribe_button.clicked.connect(self.start_transcription)
        vertical_layout_1.addWidget(self.transcribe_button)
        self.select_file_button = QPushButton("Select Video File")
        self.select_file_button.clicked.connect(self.select_video_file)
        vertical_layout_1.addWidget(self.select_file_button)
        
        # Playback controls
        self.backward_button = QPushButton("⏪")
        self.backward_button.clicked.connect(self.backward_10s)
        horizontal_layout_2.addWidget(self.backward_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.playback_button = QPushButton("⏯")
        self.playback_button.clicked.connect(self.toggle_playback)
        horizontal_layout_2.addWidget(self.playback_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.forward_button = QPushButton("⏩")
        self.forward_button.clicked.connect(self.forward_10s)
        horizontal_layout_2.addWidget(self.forward_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.sliderMoved.connect(self.set_position)
        horizontal_layout_2.addWidget(self.position_slider, 1)
        
        # Transcript display
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        vertical_layout_1.addWidget(self.output_text)
        
        # Model and speed selectors
        self.combo_box = QComboBox()
        self.combo_box.addItems(["tiny", "base", "small", "medium", "large", "turbo"])
        horizontal_layout_3.addWidget(self.combo_box)
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1.0x", "1.25x", "1.5x", "1.75x", "2.0x"])
        self.speed_combo.currentIndexChanged.connect(self.change_speed)
        horizontal_layout_3.addWidget(self.speed_combo)
        vertical_layout_1.addLayout(horizontal_layout_3)
        
        horizontal_layout_1.addLayout(vertical_layout_1, 1)
        self.setLayout(horizontal_layout_1)
        self.setWindowTitle("Video Transcriber")
        self.resize(900, 600)
        
        # Connect signals for video progress
        self.media_player.positionChanged.connect(self.update_transcription)
        self.media_player.positionChanged.connect(self.update_slider)
        self.media_player.durationChanged.connect(self.set_slider_range)
    
    def start_transcription(self):
        url = self.url_entry.text()
        if not url:
            self.output_text.setText("Please enter a video URL.")
            return
        
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
            audio_path = "audio.wav"
            
            if url_or_path.startswith("http"):
                self.output_text.setText("Downloading video...")
                download_video(url_or_path, video_path)
            
            cache_file = get_cache_path(video_path, model_name)
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    transcript = json.load(f)
            else:
                self.output_text.setText("Extracting audio...")
                extract_audio(video_path, audio_path)
                self.output_text.setText("Transcribing audio...")
                transcript = transcribe_audio(audio_path, video_path, model_name)
            
            self.output_text.setText("")
            self.transcription_segments = transcript.get("segments", [])
            self.current_index = 0
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()
            self.update_transcription(self.media_player.position())
        except Exception as e:
            self.output_text.setText(f"Error: {str(e)}")
    
    def update_transcription(self, position):
        # Simplified example: just update with the current playback time.
        current_time = position / 1000
        self.output_text.setText(f"Current time: {current_time:.2f} s")
    
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
    
    def change_speed(self):
        speed_map = {
            "1.0x": 1.0,
            "1.25x": 1.25,
            "1.5x": 1.5,
            "1.75x": 1.75,
            "2.0x": 2.0
        }
        selected_speed = self.speed_combo.currentText()
        self.media_player.setPlaybackRate(speed_map[selected_speed])
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Space:
            self.toggle_playback()
            event.accept()
        else:
            super().keyPressEvent(event)

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
        
        self.setLayout(layout)
        self.setWindowTitle("Lecture Videos")
    
    def open_video(self):
        current_item = self.video_list.currentItem()
        if current_item:
            video_identifier = current_item.text()
            # In practice, use this identifier to look up the correct video URL/path.
            self.switch_to_transcriber_callback(video_identifier)

# --- Main Window with Stacked Interface --- #
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lecture Videos Application")
        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)
        self.init_ui()
    
    def init_ui(self):
        # Create the lecture selection page
        self.selection_widget = VideoSelectionWidget(self.open_video_transcriber)
        self.stack.addWidget(self.selection_widget)
    
    def open_video_transcriber(self, video_identifier):
        # Create and display the video transcriber interface for the chosen video.
        self.transcriber_widget = VideoTranscriber(video_identifier, self.go_back_to_selection)
        # Remove old transcriber widget if already exists
        if self.stack.count() > 1:
            old_widget = self.stack.widget(1)
            self.stack.removeWidget(old_widget)
            old_widget.deleteLater()
        self.stack.addWidget(self.transcriber_widget)
        self.stack.setCurrentWidget(self.transcriber_widget)
    
    def go_back_to_selection(self):
        # Switch back to the lecture selection page.
        self.stack.setCurrentWidget(self.selection_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())
