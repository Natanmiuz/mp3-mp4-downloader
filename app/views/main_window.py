import os
import threading
from datetime import datetime
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QFrame, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QButtonGroup, QSizePolicy, QProgressBar
)
from app.core.downloader import DownloadWorker
from app.utils.helpers import get_ffmpeg_path

class VideoDownloader(QMainWindow):
    PLATFORMS = ['Auto-detect', 'YouTube', 'Facebook', 'TikTok', 'Twitter', 'Instagram', 'Any Website']
    RESOLUTIONS = ['360p', '480p', '720p', '1080p', 'Best available']

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOTNET")
        self.setMinimumSize(QSize(460, 580))
        self.resize(QSize(560, 680))
        self.worker_running = False
        self.setup_ui()
        self.setup_signals()
        self.toggle_resolution()
        self.update_ready_state()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root = QVBoxLayout(central_widget)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)
        brand_dot = QLabel("●")
        brand_dot.setObjectName("brandDot")
        title = QLabel("NOTNET")
        title.setObjectName("appTitle")
        subtitle = QLabel("Media downloader")
        subtitle.setObjectName("appSubtitle")
        header.addWidget(brand_dot)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(subtitle, alignment=Qt.AlignBottom)
        root.addLayout(header)

        # URL hero
        root.addWidget(self.section_label("LINK"))
        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlField")
        self.url_input.setPlaceholderText("Paste a video or audio URL…")
        self.url_input.setClearButtonEnabled(True)
        root.addWidget(self.url_input)

        # Source / Resolution grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(self.PLATFORMS)
        self.platform_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        grid.addWidget(self.section_label("SOURCE"), 0, 0)
        grid.addWidget(self.platform_combo, 1, 0)

        res_col = QWidget()
        res_layout = QVBoxLayout(res_col)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.setSpacing(4)
        self.res_label = self.section_label("RESOLUTION")
        self.res_combo = QComboBox()
        self.res_combo.addItems(self.RESOLUTIONS)
        self.res_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        res_layout.addWidget(self.res_label)
        res_layout.addWidget(self.res_combo)

        self.audio_note = QLabel("MP3 · 192 kbps · pulled from the best audio track")
        self.audio_note.setProperty("class", "note")
        self.audio_note.setWordWrap(True)
        self.audio_note.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        grid.addWidget(res_col, 0, 1, 2, 1)
        grid.addWidget(self.audio_note, 0, 1, 2, 1)
        root.addLayout(grid)

        # Audio / Video mode switch
        root.addWidget(self.section_label("FORMAT"))
        seg_frame = QFrame()
        seg_frame.setObjectName("segmented")
        seg_layout = QHBoxLayout(seg_frame)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(0)

        self.format_group = QButtonGroup(self)
        self.audio_btn = QPushButton("♪  Audio")
        self.audio_btn.setCheckable(True)
        self.audio_btn.setProperty("format", "mp3")
        self.video_btn = QPushButton("▶  Video")
        self.video_btn.setCheckable(True)
        self.video_btn.setProperty("format", "mp4")
        for button in (self.audio_btn, self.video_btn):
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            seg_layout.addWidget(button)
            self.format_group.addButton(button)
        self.video_btn.setChecked(True)
        root.addWidget(seg_frame)

        # Save to
        root.addWidget(self.section_label("SAVE TO"))
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("Choose a folder…")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(self.browse_btn)
        root.addLayout(path_row)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn = QPushButton("Download")
        self.download_btn.setProperty("variant", "primary")
        self.download_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        actions.addWidget(self.clear_btn)
        actions.addWidget(self.download_btn, 2)
        root.addLayout(actions)

        # Progress panel
        panel = QFrame()
        panel.setObjectName("progressPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 16, 18, 16)
        panel_layout.setSpacing(10)

        top = QHBoxLayout()
        self.stage_label = QLabel("Ready")
        self.stage_label.setObjectName("stageLabel")
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("percentLabel")
        top.addWidget(self.stage_label)
        top.addStretch(1)
        top.addWidget(self.percent_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.speed_label = QLabel("—")
        self.speed_label.setObjectName("speedLabel")
        self.speed_label.setWordWrap(True)
        self.open_folder_btn = QPushButton("Open folder")
        self.open_folder_btn.setObjectName("detailsToggle")
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.details_btn = QPushButton("Details ▾")
        self.details_btn.setObjectName("detailsToggle")
        self.details_btn.setCheckable(True)
        self.details_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bottom.addWidget(self.speed_label)
        bottom.addStretch(1)
        bottom.addWidget(self.open_folder_btn)
        bottom.addWidget(self.details_btn)

        self.log_output = QTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(130)
        self.log_output.hide()

        panel_layout.addLayout(top)
        panel_layout.addWidget(self.progress_bar)
        panel_layout.addLayout(bottom)
        panel_layout.addWidget(self.log_output)

        root.addWidget(panel)
        self.progress_panel = panel
        self.progress_panel.hide()
        root.addStretch(1)

    def section_label(self, text):
        label = QLabel(text)
        label.setProperty("class", "section-label")
        return label

    def setup_signals(self):
        self.clear_btn.clicked.connect(self.clear_fields)
        self.download_btn.clicked.connect(self.start_download)
        self.browse_btn.clicked.connect(self.browse_directory)
        self.open_folder_btn.clicked.connect(self.open_download_directory)
        self.details_btn.clicked.connect(self.toggle_details)
        self.format_group.buttonClicked.connect(self.toggle_resolution)
        self.platform_combo.currentTextChanged.connect(self.toggle_resolution)
        self.url_input.textChanged.connect(self.update_ready_state)
        self.path_input.textChanged.connect(self.update_ready_state)

    def toggle_resolution(self):
        is_mp4 = self.format_group.checkedButton().property("format") == "mp4"
        generic = self.platform_combo.currentText() == "Any Website"
        show_res = is_mp4 and not generic
        res_col = self.res_combo.parentWidget()
        res_col.setVisible(show_res)
        self.res_combo.setEnabled(show_res)
        self.audio_note.setVisible(not is_mp4)

    def update_ready_state(self):
        if self.worker_running:
            return
        ready = bool(self.url_input.text().strip()) and bool(self.path_input.text().strip())
        self.download_btn.setEnabled(ready)

    def toggle_details(self):
        if self.details_btn.isChecked():
            self.log_output.show()
            self.details_btn.setText("Details ▴")
        else:
            self.log_output.hide()
            self.details_btn.setText("Details ▾")

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_path = directory
            self.path_input.setText(directory)

    def clear_fields(self):
        self.url_input.clear()
        self.platform_combo.setCurrentIndex(0)
        self.video_btn.setChecked(True)
        self.res_combo.setCurrentIndex(0)
        self.path_input.clear()
        self.log_output.clear()
        self.download_btn.setText("Download")
        self.progress_panel.hide()
        self.toggle_resolution()
        self.update_ready_state()

    def validate_inputs(self):
        if not self.url_input.text().strip():
            QMessageBox.critical(self, "Error", "Please enter a valid URL!")
            return False
        if not self.path_input.text().strip():
            QMessageBox.critical(self, "Error", "Please select a download directory!")
            return False
        if self.format_group.checkedButton().property("format") == "mp4":
            ffmpeg_path = get_ffmpeg_path()
            if not os.path.isfile(ffmpeg_path):
                QMessageBox.critical(self, "Error", "FFmpeg not found. Required for video processing!")
                return False
        return True

    def start_download(self):
        if not self.validate_inputs():
            return

        self.worker_running = True
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading…")
        self.reset_progress()

        self.worker = DownloadWorker(
            self.url_input.text().strip(),
            self.platform_combo.currentText(),
            self.format_group.checkedButton().property("format"),
            self.res_combo.currentText(),
            self.path_input.text(),
            get_ffmpeg_path()
        )
        self.worker.signals.update_progress.connect(self.update_status)
        self.worker.signals.progress_updated.connect(self.on_progress)
        self.worker.signals.download_complete.connect(self.download_complete)
        self.worker.signals.error_occurred.connect(self.handle_error)

        self.download_thread = threading.Thread(target=self.worker.run, daemon=True)
        self.download_thread.start()

    def reset_progress(self):
        self.progress_bar.setValue(0)
        self.percent_label.setText("0%")
        self.speed_label.setText("—")
        self.stage_label.setText("Downloading…")
        for widget in (self.stage_label, self.percent_label, self.progress_bar):
            widget.setProperty("state", "downloading")
        self.repolish(self.stage_label, self.percent_label, self.progress_bar)
        self.details_btn.setChecked(False)
        self.log_output.clear()
        self.log_output.hide()
        self.details_btn.setText("Details ▾")
        self.progress_panel.show()

    def on_progress(self, percent, speed, eta):
        if percent is not None and percent >= 0:
            value = min(100, int(round(percent)))
            self.progress_bar.setValue(value)
            self.percent_label.setText(f"{value}%")
            if value >= 100 and not speed:
                self.stage_label.setText("Finalizing…")
        if speed:
            text = speed
            if eta:
                text += f" · {eta} left"
            self.speed_label.setText(text)

    def download_complete(self):
        self.worker_running = False
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Download")
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.stage_label.setText("Completed")
        for widget in (self.stage_label, self.percent_label, self.progress_bar):
            widget.setProperty("state", "success")
        self.repolish(self.stage_label, self.percent_label, self.progress_bar)
        self.speed_label.setText("Saved to " + self.path_input.text())

    def handle_error(self, message):
        self.worker_running = False
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Download")
        self.stage_label.setText("Download failed")
        for widget in (self.stage_label, self.percent_label, self.progress_bar):
            widget.setProperty("state", "error")
        self.repolish(self.stage_label, self.percent_label, self.progress_bar)
        self.speed_label.setText("Check the details below")
        self.log_output.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.details_btn.setChecked(True)
        self.log_output.show()
        self.details_btn.setText("Details ▴")

    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")
        self.log_output.ensureCursorVisible()

    def repolish(self, *widgets):
        for widget in widgets:
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def open_download_directory(self):
        path = self.path_input.text()
        if os.path.isdir(path):
            try:
                os.startfile(path)
            except AttributeError:
                self.update_status(f"Download directory: {path}")
