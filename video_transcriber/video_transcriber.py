import os, whisper, ffmpeg, json

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox, 
                             QFileDialog, QHBoxLayout, QSlider)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtCore import QUrl, Qt, QTimer

from cache_handler import *
from video_downloader import *
from settings_window import *

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

def transcribe_audio(audio_path, video_path,model_name):
    """Check cache before running Whisper AI and save transcription if not cached."""
    cache_file = get_cache_path(video_path, model_name)
    
    print("Running Whisper AI...")
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path)

    # Save the result in cache
    with open(cache_file, "w") as f:
        json.dump(result, f)

    return result

class VideoTranscriber(QWidget):
    def __init__(self, video_identifier, switch_back_callback):
        super().__init__()

        self.switch_back_callback = switch_back_callback
        self.video_identifier = video_identifier  # Could be a URL, file path, or lecture title
        
        self.init_ui()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
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
        
        # TODO: Directly set video path
        self.url_entry = QLineEdit()
        self.url_entry.setText(self.video_identifier)
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

        # Whisper model Selection
        self.combo_box = QComboBox()
        self.combo_box.addItems(["tiny", "base", "small", "medium", "large", "turbo"])
        horizontal_layout_3.addWidget(self.combo_box)

        # Playback Speed Selection
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["1.0x", "1.25x", "1.5x", "1.75x", "2.0x"])
        self.speed_combo.currentIndexChanged.connect(self.change_speed)
        horizontal_layout_3.addWidget(self.speed_combo)
        vertical_layout_1.addLayout(horizontal_layout_3)

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
                download_video(url_or_path, video_path) # TODO: change with cached path
            
            # Check for cache
            cache_file = get_cache_path(video_path, model_name)
            print(cache_file)
            if os.path.exists(cache_file):
                print(f"Loading cached transcription: {cache_file}")
                with open(cache_file, "r") as f:
                    transcript = json.load(f)  # Load cached transcription
            else : # If not cached, extract audio and transcribe
                self.output_text.setText("Extracting audio...")
                extract_audio(video_path, audio_path)
                
                self.output_text.setText("Transcribing audio...")
                transcript = transcribe_audio(audio_path, video_path, model_name)
            
            self.output_text.setText("")
            self.transcription_segments = transcript["segments"]
            self.current_index = 0
            self.media_player.setSource(QUrl.fromLocalFile(video_path))
            self.media_player.play()
            # self.update_transcription() # BUG: Causes crash we reloading the page
        except Exception as e:
            self.output_text.setText(f"Error: {str(e)}")

    def update_transcription(self, position):
        """
        Rebuild the transcript so that:
          - Before first segment starts: all gray.
          - After last segment ends: all white.
          - In a gap between segments: segments with end < current_time are white; others gray.
          - While inside a segment: previous segments white, current segment split (white/ cyan/ gray), future gray.

        Always scroll so that up to 10 “white” lines are visible above (i.e. scroll to anchor max(0, last_spoken_index-10)).
        """
        current_time = position / 1000.0  # ms → seconds
        segments = self.transcription_segments

        # 1) Try to find an active segment (where start ≤ current_time ≤ end)
        active_index = None
        for i, seg in enumerate(segments):
            if seg["start"] <= current_time <= seg["end"]:
                active_index = i
                break

        # 2) Find the index of the last‐spoken segment (i.e. seg.end < current_time).  
        #    If none, last_spoken = -1.
        last_spoken = -1
        for i, seg in enumerate(segments):
            if seg["end"] < current_time:
                last_spoken = i

        fs = load_settings().get("font_size", 12)

        # 3a) Case A: before the very first segment starts
        if active_index is None and current_time < segments[0]["start"]:
            html = f"<div style='font-size: {fs}px;'>"
            for i, s in enumerate(segments):
                html += (
                    f"<a name='seg_{i}'></a>"
                    f"<span style='color:gray;'>{s['text']}</span> "
                )
            html += "</div>"

            self.output_text.setHtml(html)
            # Nothing is white yet, so last_spoken = -1; scroll to 0 (max(0, -1 - 10) → 0)
            self.output_text.scrollToAnchor("seg_0")
            return

        # 3b) Case B: after the very last segment ends
        if current_time > segments[-1]["end"]:
            html = f"<div style='font-size: {fs}px;'>"
            for i, s in enumerate(segments):
                html += (
                    f"<a name='seg_{i}'></a>"
                    f"<span style='color:white;'>{s['text']}</span> "
                )
            html += "</div>"

            self.output_text.setHtml(html)
            # last_spoken = len(segments)-1, so scroll_anchor = max(0, last_spoken-10)
            scroll_anchor = max(0, len(segments) - 1 - 10)
            self.output_text.scrollToAnchor(f"seg_{scroll_anchor}")
            return

        # 3c) Case C: we are in a gap between segments (no active_index, but not before first or after last)
        if active_index is None:
            # Build HTML: segments 0..last_spoken in white; (last_spoken+1)..end in gray
            html = f"<div style='font-size: {fs}px;'>"
            for i, s in enumerate(segments):
                html += f"<a name='seg_{i}'></a>"
                if i <= last_spoken:
                    html += f"<span style='color:white;'>{s['text']}</span> "
                else:
                    html += f"<span style='color:gray;'>{s['text']}</span> "
            html += "</div>"

            self.output_text.setHtml(html)
            scroll_anchor = max(0, last_spoken - 10)
            self.output_text.scrollToAnchor(f"seg_{scroll_anchor}")
            return

        # 4) Case D: We do have an active segment at active_index
        seg = segments[active_index]
        words = seg["text"].split()
        elapsed = current_time - seg["start"]
        dur = seg["end"] - seg["start"]
        widx = int((elapsed / dur) * len(words))
        widx = min(widx, len(words) - 1)

        prev_words = " ".join(words[:widx])
        active_word = words[widx]
        next_words = " ".join(words[widx + 1 :])

        # Build the full HTML:
        #   - For i < active_index: already said → white
        #   - For i == active_index: split into white/ cyan/ gray
        #   - For i > active_index: future → gray
        full_html = f"<div style='font-size: {fs}px;'>"
        for i, s in enumerate(segments):
            full_html += f"<a name='seg_{i}'></a>"
            if i < active_index:
                full_html += f"<span style='color:white;'>{s['text']}</span> "
            elif i == active_index:
                # Three‐color split for the active segment
                seg_html = (
                    f"<span>"
                    f"<span style='color:white;'>{prev_words} </span>"
                    f"<span style='color:cyan;'>{active_word} </span>"
                    f"<span style='color:gray;'>{next_words}</span>"
                    f"</span> "
                )
                full_html += seg_html
            else:
                full_html += f"<span style='color:gray;'>{s['text']}</span> "
        full_html += "</div>"

        self.output_text.setHtml(full_html)

        # Now, scroll so that up to 10 “white” segments above the active one remain visible.
        scroll_anchor = max(0, active_index - 10)
        self.output_text.scrollToAnchor(f"seg_{scroll_anchor}")

        # Optional nudge: if you want the active segment slightly more centered,
        # uncomment the lines below. Otherwise, you can remove them.
        cursor = self.output_text.textCursor()
        doc = self.output_text.document()
        found = doc.find(f"seg_{active_index}", 0)
        if not found.isNull():
            self.output_text.setTextCursor(found)
            self.output_text.centerCursor()

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