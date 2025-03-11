import sys, os
import feedparser  # For parsing the RSS feed
import requests    # For downloading videos

from cache_handler import *
from video_selection import *  # Your existing widget for cached videos
from video_transcriber import *
from help_window import *
from settings_window import *

from PyQt6.QtWidgets import (QApplication, QWidget, QStackedWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel,
                             QMainWindow, QDialog, QTextBrowser, QPushButton, QHBoxLayout, QAction, QMessageBox)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

# URL for the RSS feed
RSS_FEED_URL = "https://video.ethz.ch/lectures/d-infk/2025/spring/252-0220-00L.rss.xml?key=e01439&quality=HIGH"

# --- New Widget for RSS Video Selection --- #
class RSSVideoSelectionWidget(QWidget):
    def __init__(self, on_video_selected, parent=None):
        super().__init__(parent)
        self.on_video_selected = on_video_selected
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Browse Videos from RSS Feed"))
        self.video_list = QListWidget()
        layout.addWidget(self.video_list)
        self.video_list.itemClicked.connect(self.handle_item_clicked)
        self.populate_video_list()

    def populate_video_list(self):
        feed = feedparser.parse(RSS_FEED_URL)
        if feed.bozo:
            print("Error parsing RSS feed:", feed.bozo_exception)
            return

        for entry in feed.entries:
            title = entry.get("title", "No title")
            # Look for a video URL – check if there's an enclosure first
            video_url = ""
            if "enclosures" in entry and entry.enclosures:
                video_url = entry.enclosures[0].get("href", "")
            else:
                video_url = entry.get("link", "")
            item = QListWidgetItem(title)
            item.setData(Qt.ItemDataRole.UserRole, video_url)
            self.video_list.addItem(item)

    def handle_item_clicked(self, item):
        video_url = item.data(Qt.ItemDataRole.UserRole)
        self.on_video_selected(video_url)

# --- Modified Home Widget --- #
class HomeWidget(QWidget):
    def __init__(self, on_video_selected, parent=None):
        super().__init__(parent)
        self.on_video_selected = on_video_selected
        layout = QVBoxLayout(self)
        
        # --- Recent Cached Videos Section --- #
        layout_horizontal = QHBoxLayout()
        layout_horizontal.addWidget(QLabel("Recently Cached Videos"))
        help_button = QPushButton("?")
        help_button.clicked.connect(self.open_help_dialog)
        layout_horizontal.addWidget(help_button, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(layout_horizontal)

        self.recent_list = QListWidget()
        self.recent_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.recent_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.recent_list.setMovement(QListWidget.Movement.Static)
        self.recent_list.setIconSize(QSize(160, 90))  # Adjust size as needed
        self.populate_recent_videos()
        self.recent_list.itemClicked.connect(self.handle_item_clicked)
        layout.addWidget(self.recent_list)
        
        # --- Cached Videos Selection Widget (existing) --- #
        layout.addWidget(QLabel("Browse Cached Videos"))
        self.cached_selection_widget = VideoSelectionWidget(self.on_video_selected)
        layout.addWidget(self.cached_selection_widget)
        
        # --- RSS Video Selection Widget --- #
        layout.addWidget(QLabel("Browse Videos from RSS Feed"))
        self.rss_selection_widget = RSSVideoSelectionWidget(self.on_video_selected)
        layout.addWidget(self.rss_selection_widget)

    def populate_recent_videos(self):
        videos_dir = os.path.join(get_cache_video_path(), "videos")
        if not os.path.exists(videos_dir):
            print("Videos directory does not exist:", videos_dir)
            return

        video_files = [f for f in os.listdir(videos_dir)
                       if os.path.isfile(os.path.join(videos_dir, f)) and
                       f.lower().endswith((".mp4", ".avi", ".mkv", ".mov"))]

        for video in video_files:
            video_path = os.path.join(videos_dir, video)
            thumbnail_path = os.path.splitext(video_path)[0] + ".png"
            if not os.path.exists(thumbnail_path):
                thumbnail_path = "default_thumbnail.png"
            item = QListWidgetItem()
            item.setIcon(QIcon(thumbnail_path))
            item.setText(video)
            item.setData(Qt.ItemDataRole.UserRole, video_path)
            self.recent_list.addItem(item)

    def handle_item_clicked(self, item):
        video_path = item.data(Qt.ItemDataRole.UserRole)
        self.on_video_selected(video_path)
    
    def open_help_dialog(self):
        dialog = HelpSection()
        dialog.exec()

# --- Video Download Helper Function --- #
def download_video(video_url, save_path):
    try:
        response = requests.get(video_url, stream=True)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        with open(save_path, 'wb') as f:
            downloaded = 0
            for data in response.iter_content(chunk_size=1024):
                downloaded += len(data)
                f.write(data)
                # Optionally update progress here
                print(f"Downloaded {downloaded} of {total} bytes", end='\r')
        print("\nDownload complete:", save_path)
    except Exception as e:
        print("Error downloading video:", e)
        QMessageBox.critical(None, "Download Error", f"An error occurred: {e}")

# --- Main Window --- #
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()  # Load settings from file
        self.setWindowTitle("Lecture Videos Application")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.init_ui()

    def init_ui(self):
        self.home_widget = HomeWidget(self.open_video_transcriber)
        self.stack.addWidget(self.home_widget)
        self.create_menu()

    def create_menu(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        pref_action = QAction("Preferences", self)
        pref_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(pref_action)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            save_settings(self.settings)
            current_widget = self.stack.currentWidget()
            if hasattr(current_widget, "apply_settings"):
                current_widget.apply_settings(self.settings)

    def open_video_transcriber(self, video_identifier):
        # If video_identifier is a URL, ask the user if they want to download it
        if video_identifier.startswith("http"):
            reply = QMessageBox.question(
                self, "Download Video",
                f"Do you want to download the video from:\n{video_identifier}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                videos_dir = os.path.join(get_cache_video_path(), "videos")
                os.makedirs(videos_dir, exist_ok=True)
                filename = os.path.basename(video_identifier)
                if not filename:
                    filename = "downloaded_video.mp4"
                save_path = os.path.join(videos_dir, filename)
                download_video(video_identifier, save_path)
                video_identifier = save_path

        self.transcriber_widget = VideoTranscriber(video_identifier, self.go_back_to_selection)
        if self.stack.count() > 1:
            old_widget = self.stack.widget(1)
            self.stack.removeWidget(old_widget)
            old_widget.deleteLater()
        self.stack.addWidget(self.transcriber_widget)
        self.stack.setCurrentWidget(self.transcriber_widget)

    def go_back_to_selection(self):
        self.stack.setCurrentWidget(self.home_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec())
