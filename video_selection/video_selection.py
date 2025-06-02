import os, json, ffmpeg, whisper, feedparser, shutil

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QListWidget, QDialog, QLineEdit,
    QLabel, QCheckBox, QFileDialog, QHBoxLayout, QListWidgetItem, QProgressBar
)
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtCore import Qt

from cache_handler import *
from video_downloader import *
from settings_window import *
from video_transcriber import *

# Supported Whisper models
MODELS = ["tiny", "base", "small", "medium", "large", "turbo"]

class RSSVideoSelectionWidget(QWidget):
    """
    Shows a checkable, multi-select list of videos from cached RSS feeds,
    with batch actions and color-coding:
      - White: transcript exists
      - Grey: downloaded but not transcribed
      - Red: not downloaded
    """
    def __init__(self, filename, switch_to_transcriber_callback, parent=None):
        super().__init__()
        self.filename = filename
        self.switch_to_transcriber_callback = switch_to_transcriber_callback
        self.init_ui()
        self.populate_list()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Buttons for batch operations
        btn_layout = QHBoxLayout()
        self.download_btn = QPushButton("Download Selected")
        self.delete_btn = QPushButton("Delete Selected")
        self.select_all_btn = QPushButton("Select All")
        btn_layout.addWidget(self.download_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.select_all_btn)
        layout.addLayout(btn_layout)

        # Video list
        self.video_list = QListWidget()
        self.video_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        layout.addWidget(self.video_list)
        # self.populate_list()

        # Connect signals
        self.download_btn.clicked.connect(self.download_selected)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.select_all_btn.clicked.connect(self.select_all)
        self.video_list.itemClicked.connect(self.on_item_clicked)
        self.video_list.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.setLayout(layout)

    def populate_list(self):
        self.video_list.clear()
        if not os.path.exists(self.filename):
            return

        with open(self.filename, "r", encoding="utf-8") as f:
            feed_data = json.load(f)

        for entry in feed_data.get("entries", []):
            title = entry.get("title", "Missing title")
            date = entry.get("published_parsed")
            date_str = f"_{date[2]}-{date[1]}-{date[0]}" if date else ""
            key = ''.join(c for c in title if c.isupper()) + date_str
            url = entry.get("link")
            if not url:
                continue

            item = QListWidgetItem(key)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, url)

            # Paths
            video_path = os.path.join(VIDEO_DIR, f"{key}.mp4")
            # Look for any transcript file matching key_model.json
            transcript_exists = False
            if os.path.isdir(TRANSCRIPT_DIR):
                for fname in os.listdir(TRANSCRIPT_DIR):
                    base, ext = os.path.splitext(fname)
                    if ext.lower() == ".json" and base.startswith(f"{key}_"):
                        # Check suffix matches model
                        suffix = base[len(key) + 1:]
                        if suffix in MODELS:
                            transcript_exists = True
                            break

            # Color based on status
            if os.path.exists(video_path) and transcript_exists:
                item.setForeground(QColor("white"))
            elif os.path.exists(video_path):
                item.setForeground(QColor("grey"))
            else:
                item.setForeground(QColor("red"))

            self.video_list.addItem(item)

    def uncheck_all(self):
        for i in range(self.video_list.count()):
            self.video_list.item(i).setCheckState(Qt.CheckState.Unchecked)

    def select_all(self):
        count = self.video_list.count()
        all_checked = all(
            self.video_list.item(i).checkState() == Qt.CheckState.Checked
            for i in range(count)
        )
        new_state = Qt.CheckState.Unchecked if all_checked else Qt.CheckState.Checked
        for i in range(count):
            self.video_list.item(i).setCheckState(new_state)

    def download_selected(self):
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                url = item.data(Qt.ItemDataRole.UserRole)
                key = item.text()
                video_path = os.path.join(VIDEO_DIR, f"{key}.mp4")
                if not os.path.exists(video_path):
                    download_video(url, video_path)
        self.uncheck_all()
        self.populate_list()

    def delete_selected(self):
        for i in range(self.video_list.count()):
            item = self.video_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                key = item.text()
                video_path = os.path.join(VIDEO_DIR, f"{key}.mp4")
                # Eliminate video
                if os.path.exists(video_path):
                    os.remove(video_path)

                # Eliminate transcript
                for fname in os.listdir(TRANSCRIPT_DIR):
                    base, ext = os.path.splitext(fname)
                    if ext.lower() == ".json" and base.startswith(f"{key}_"):
                        # Check suffix matches model
                        suffix = base[len(key) + 1:]
                        if suffix in MODELS:
                            os.remove(TRANSCRIPT_DIR + key + "_" + suffix + ".json")
        self.uncheck_all()
        self.populate_list()

    def on_item_clicked(self, item: QListWidgetItem):
        """Single-click: toggle checkbox"""
        # invert check state
        new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
        item.setCheckState(new_state)

    def on_item_double_clicked(self, item: QListWidgetItem):
        """Double-click: open video if it's downloaded"""
        # Retrieve the video URL from the clicked item.
        name_entry = item.data(Qt.ItemDataRole.UserRole + 1)
        video_url = item.data(Qt.ItemDataRole.UserRole)
        key = item.text()
        video_path = os.path.join(VIDEO_DIR, f"{key}.mp4")
        if os.path.exists(video_path):
            self.switch_to_transcriber_callback(video_path)
        else :
            dialog = AddVideoDialog()
            dialog.name_entry.setText(name_entry)
            dialog.url_entry.setText(video_url)
            dialog.exec()

class AddRSSDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add RSS")
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout_horizontal = QHBoxLayout()
        
        # URL input
        self.url_rss = QLineEdit()
        self.url_rss.setPlaceholderText("Enter RSS")
        # layout_horizontal.addWidget(QLabel("RS:"))
        layout_horizontal.addWidget(self.url_rss)

        # Confirm button - calls our custom on_confirm method
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.clicked.connect(self.on_confirm)
        layout.addWidget(self.confirm_button)

        layout.addLayout(layout_horizontal)
        self.setLayout(layout)

    # Save RSS    
    def on_confirm(self):
        feed = feedparser.parse(self.url_rss.text())
        
        title = feed.feed.get('title', "No channel title found")
        title = ''.join([c for c in title if c.isupper()]) # Use only upper cases
        if feed.bozo:
            print("Error parsing RSS feed:", feed.bozo_exception)
            return
        set_rss_cache(feed, title)
        
        # Save feed's url for future updates
        set_rss_url_cache(self.url_rss.text(), title)

        self.accept()

    def on_item_double_clicked(self, item: QListWidgetItem):
        """Open video if it's downloaded"""
        key = item.text()
        video_path = os.path.join(VIDEO_DIR, f"{key}.mp4")
        if os.path.exists(video_path):
            self.switch_to_transcriber_callback(video_path)


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
            settings = load_settings()
            model = settings.get("preferred_model", "tiny")
            if transcribe_now:
                # Use the provided video name if available; otherwise use a default.
                if not video_name or video_name.strip() == "":
                    video_name = "downloaded_video.mp4"
                self.process_video(video_path, model, 1, video_name)
            else :
                self.process_video(video_path, model, 0, video_name)

        self.accept()
    
    def process_video(self, url_or_path, model_name, transcribe, video_name="downloaded_video.mp4"):
        # Add .mp4 if video_name doesn't have it
        if video_name != "":
            if not video_name.lower().endswith(".mp4"):
                video_name += ".mp4"

        # Use video_name if downloading from a URL; otherwise, use the local file path.
        video_path = VIDEO_DIR + video_name if url_or_path.startswith("http") else url_or_path
        print("Video path to be processed:", video_path)
        audio_path = AUDIO_DIR + "audio.wav"
        self.video_path_cache = video_path

        if url_or_path.startswith("http"):
            # Check if the file already exists before downloading.
            if not os.path.exists(video_path):
                print("Downloading video...")
                download_video(url_or_path, video_path)
            else:
                print("Video already downloaded, skipping download.")
        else:
            # Copy local file in cache
            shutil.copyfile(url_or_path, VIDEO_DIR + video_name)

        cache_file = get_cache_path(video_path, model_name)
        if transcribe == 1:
            if os.path.exists(cache_file):
                print(f"Loading cached transcription: {cache_file}")
                with open(cache_file, "r") as f:
                    _ = json.load(f)
            else:
                print("Extracting audio...")
                self.extract_audio(video_path, audio_path)
                print("Transcribing audio...")
                _ = self.transcribe_audio(audio_path, video_path, model_name)
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
        self.rss_widget_open = 0
        self.rss_widget_store = ''
        self.refresh_rss_list()
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        layout_horizontal = QHBoxLayout()
        self.video_list = QListWidget()

        if not os.path.exists(RSS_DIR):
            return

        # Loop through all cached RSS JSON files.
        for filename in os.listdir(RSS_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(RSS_DIR, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    feed_data = json.load(f)
                    # Get the list of entries
                    feed_entries = feed_data.get('entries', [])
                    if feed_entries:
                        # Access the first entry and extract its title
                        title = feed_entries[0].get('title', "Missing title")
                    else:
                        title = "Missing title"

                    # TODO: Add number of how many videos are not cached

                    
                    item = QListWidgetItem(title)
                    item.setData(Qt.ItemDataRole.UserRole, file_path)
                    self.video_list.addItem(item)

        self.layout.addWidget(self.video_list)
        self.video_list.itemClicked.connect(self.feed_clicked)
        
        # open_button = QPushButton("Open Selected Lecture")
        # open_button.clicked.connect(self.open_video)
        # layout_horizontal.addWidget(open_button)
        
        open_button = QPushButton("Save RSS")
        open_button.clicked.connect(self.open_add_RSS_dialog)
        layout_horizontal.addWidget(open_button)

        add_video_button = QPushButton("Save Video")
        add_video_button.clicked.connect(self.open_add_video_dialog)
        layout_horizontal.addWidget(add_video_button)
        
        self.layout.addLayout(layout_horizontal)
        self.setLayout(self.layout)
        self.setWindowTitle("Lecture Videos")   
    
    def refresh_rss_list(self):
        if not os.path.exists(URL_DIR):
            return
        
        # Use feedparser to update the rss
        for filename in os.listdir(URL_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(URL_DIR, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        feed_url = json.load(f)
                    feed = feedparser.parse(feed_url)
                    
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    title = "Error loading feed"
                
                title = feed.feed.get('title', "No channel title found")
                title = ''.join([c for c in title if c.isupper()]) # Use only upper cases
                if feed.bozo:
                    print("Error parsing RSS feed:", feed.bozo_exception)
                    return
                set_rss_cache(feed, title)

    def open_add_RSS_dialog(self):
        dialog = AddRSSDialog()
        dialog.exec()
        
    def open_add_video_dialog(self):
        dialog = AddVideoDialog()
        if dialog.exec():
            video_path, transcribe_now, _ = dialog.get_video_data()
            if video_path:
                self.video_list.addItem(video_path)  # Add to the list
                if transcribe_now:
                    self.switch_to_transcriber_callback(video_path)

    def feed_clicked(self, item):
        """When a feed is clicked, load its lessons and display them below."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                feed_data = json.load(f)
        except Exception as e:
            print(f"Error loading feed {file_path}: {e}")
            return
        
        # Create an instance of RSSVideoSelectionWidget with the file_path.
        rss_widget = RSSVideoSelectionWidget(file_path, self.switch_to_transcriber_callback)
        if self.rss_widget_open == 1:
            self.layout.removeWidget(self.rss_widget_store)

        self.layout.addWidget(rss_widget)
        self.rss_widget_store = rss_widget
        self.rss_widget_open = 1