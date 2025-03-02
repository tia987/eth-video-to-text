from video_transcriber import *
from video_selection import *

from PyQt6.QtWidgets import (QVBoxLayout,QPushButton, QLabel, QHBoxLayout, QComboBox, QSpinBox, QDialog
)

# --- Settings Dialog --- #
class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.current_settings = current_settings
        layout = QVBoxLayout(self)

        # Font Size setting
        font_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 40)
        self.font_spin.setValue(self.current_settings.get("font_size", 12))
        font_layout.addWidget(font_label)
        font_layout.addWidget(self.font_spin)
        layout.addLayout(font_layout)

        # Preferred Model setting
        model_layout = QHBoxLayout()
        model_label = QLabel("Preferred Model:")
        self.model_combo = QComboBox()
        models = ["tiny", "base", "small", "medium", "large", "turbo"]
        self.model_combo.addItems(models)
        self.model_combo.setCurrentText(self.current_settings.get("preferred_model", "tiny"))
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)

        # OK and Cancel buttons
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
    
    def get_settings(self):
        return {
            "font_size": self.font_spin.value(),
            "preferred_model": self.model_combo.currentText()
        }
    