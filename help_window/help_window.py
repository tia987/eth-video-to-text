import os

from PyQt6.QtWidgets import (QVBoxLayout, QDialog, QTextBrowser)

class HelpSection(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help")
        self.resize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create a text browser to display Markdown as formatted text
        self.text_display = QTextBrowser()
        self.text_display.setOpenExternalLinks(True)  # Enable links if needed

        # Load and display help text as Markdown
        help_text = self.load_help_text()
        self.text_display.setMarkdown(help_text)  # Apply Markdown formatting

        layout.addWidget(self.text_display)
        self.setLayout(layout)
    
    def load_help_text(self):
        help_file_path = os.path.join("help_window", "help.txt")
        if os.path.exists(help_file_path):
            with open(help_file_path, "r", encoding="utf-8") as file:
                return file.read()
        else:
            return "Help file not found. Please make sure 'config/help.txt' exists."
