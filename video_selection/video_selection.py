from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget)
from PyQt6.QtGui import QAction

from cache_handler import *

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
        
    def create_menu(self):
        # Create a menu bar with a Settings menu
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        pref_action = QAction("Preferences", self)
        pref_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(pref_action)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            # If the current page is the transcriber, update its settings.
            current_widget = self.stack.currentWidget()
            if isinstance(current_widget, VideoTranscriber):
                current_widget.apply_settings(self.settings)

    
    def open_video(self):
        current_item = self.video_list.currentItem()
        if current_item:
            video_identifier = current_item.text()
            # In practice, use this identifier to look up the correct video URL/path.
            self.switch_to_transcriber_callback(video_identifier)