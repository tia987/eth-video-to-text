import sys, os, feedparser

from cache_handler import *
from video_selection import *
from video_transcriber import *
from help_window import *
from settings_window import *

from PyQt6.QtWidgets import (QApplication, QWidget, QStackedWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel,
                             QMainWindow, QDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize

# --- New Widget for Home Page with Recent Videos --- #
class HomeWidget(QWidget):
    def __init__(self, on_video_selected, parent=None):
        super().__init__(parent)
        self.on_video_selected = on_video_selected
        layout = QVBoxLayout(self)
        layout_horizontal = QHBoxLayout(self)

        # Create a label and a horizontal list (in icon mode) for recent videos.
        layout_horizontal.addWidget(QLabel("Recently Cached Videos"))
        self.recent_list = QListWidget()
        self.recent_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.recent_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.recent_list.setMovement(QListWidget.Movement.Static)
        self.recent_list.setIconSize(QSize(160, 90))  # Adjust size as needed

        # layout_horizontal.addWidget(QLabel("?"))
        help_window = QPushButton("?")
        help_window.clicked.connect(self.open_help_dialog)
        layout_horizontal.addWidget(help_window, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(layout_horizontal)

        # Populate recent videos by scanning the cache/videos folder.
        self.populate_recent_videos()
        self.recent_list.itemClicked.connect(self.handle_item_clicked)
        layout.addWidget(self.recent_list)

        # Optionally, add the existing video selection widget below the recent videos.
        layout.addWidget(QLabel("RSS Feeds"))
        self.selection_widget = VideoSelectionWidget(self.on_video_selected)
        layout.addWidget(self.selection_widget)

    def populate_recent_videos(self):
        # Construct the videos directory path.
        videos_dir = os.path.join(get_cache_video_path(), "videos")
        if not os.path.exists(videos_dir):
            print("Videos directory does not exist:", videos_dir)
            return

        # List video files with common extensions.
        video_files = [f for f in os.listdir(videos_dir)
                       if os.path.isfile(os.path.join(videos_dir, f)) and
                       f.lower().endswith((".mp4", ".avi", ".mkv", ".mov"))]

        for video in video_files:
            video_path = os.path.join(videos_dir, video)
            # Try to load a thumbnail with the same base name and .png extension.
            thumbnail_path = os.path.splitext(video_path)[0] + ".png"
            if not os.path.exists(thumbnail_path):
                # Optionally, use a default thumbnail if one is not found.
                thumbnail_path = "default_thumbnail.png"

            item = QListWidgetItem()
            item.setIcon(QIcon(thumbnail_path))
            item.setText(video)
            # Store the full video path as the identifier.
            item.setData(Qt.ItemDataRole.UserRole, video_path)
            self.recent_list.addItem(item)

    def handle_item_clicked(self, item):
        video_path = item.data(Qt.ItemDataRole.UserRole)
        self.on_video_selected(video_path)
    
    def open_help_dialog(self):
        dialog = HelpSection()
        dialog.exec()

# --- Main Window with Menu and Stacked Interface --- #
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()  # Load settings from file
        self.setWindowTitle("Video Lectures Aggregator")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.init_ui()

    def init_ui(self):
        # Create the home page that includes the recent videos list and video selection.
        self.home_widget = HomeWidget(self.open_video_transcriber)
        self.stack.addWidget(self.home_widget)
        self.create_menu()

    def create_menu(self):
        # Create a menu bar with a Settings menu.
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        pref_action = QAction("Preferences", self)
        pref_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(pref_action)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            save_settings(self.settings)  # Save settings to file
            # If the current page is the transcriber, update its settings.
            current_widget = self.stack.currentWidget()
            if hasattr(current_widget, "apply_settings"):
                current_widget.apply_settings(self.settings)

    def open_video_transcriber(self, video_identifier):
        # Create the video transcriber interface with the current settings.
        self.transcriber_widget = VideoTranscriber(video_identifier, self.go_back_to_selection)
        # Remove any old transcriber widget.
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