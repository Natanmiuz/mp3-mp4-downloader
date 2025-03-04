import os
import threading
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QRadioButton, QGroupBox, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QButtonGroup, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from app.core.downloader import DownloadWorker, DownloadSignals
from app.utils.styles import MAIN_WINDOW_STYLES
from app.utils.helpers import get_ffmpeg_path

class VideoDownloader(QMainWindow):
    PLATFORMS = ['Auto-detect', 'YouTube', 'Facebook', 'TikTok', 'Twitter']
    FORMATS = [('MP4', 'mp4'), ('MP3', 'mp3')]
    RESOLUTIONS = ['360p', '480p', '720p', '1080p', 'Best available']
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOTNET - Video Downloader")
        self.setMinimumSize(QSize(400, 500))
        self.setup_ui()
        self.setup_signals()
        self.download_thread = None
        self.download_path = ""
        self.setStyleSheet(MAIN_WINDOW_STYLES)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # URL Input
        url_group = QGroupBox("Video URL")
        url_layout = QHBoxLayout(url_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video URL here...")
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        url_layout.addWidget(self.url_input)

        # Download Options
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)
        
        # Platform Selection
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Platform:"))
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(self.PLATFORMS)
        self.platform_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        platform_layout.addWidget(self.platform_combo, 1)
        options_layout.addLayout(platform_layout)

        # Format Selection
        format_group = QGroupBox("Format")
        format_layout = QHBoxLayout(format_group)
        self.format_group = QButtonGroup(self)
        for text, value in self.FORMATS:
            rb = QRadioButton(text)
            rb.setProperty('format', value)
            format_layout.addWidget(rb)
            self.format_group.addButton(rb)
        self.format_group.buttons()[0].setChecked(True)
        options_layout.addWidget(format_group)

        # Resolution Selection
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(self.RESOLUTIONS)
        self.resolution_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        resolution_layout.addWidget(self.resolution_combo, 1)
        options_layout.addLayout(resolution_layout)

        # Download Path
        path_group = QGroupBox("Download Location")
        path_layout = QHBoxLayout(path_group)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_directory)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)

        # Control Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        self.clear_btn = QPushButton("Clear All")
        self.download_btn = QPushButton("Start Download")
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.download_btn)

        # Status Output
        status_group = QGroupBox("Download Status")
        status_layout = QVBoxLayout(status_group)
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        self.status_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        status_layout.addWidget(self.status_output)

        main_layout.addWidget(url_group)
        main_layout.addWidget(options_group)
        main_layout.addWidget(path_group)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(status_group, 1)

    def setup_signals(self):
        self.clear_btn.clicked.connect(self.clear_fields)
        self.download_btn.clicked.connect(self.start_download)
        self.format_group.buttonClicked.connect(self.toggle_resolution)

    def resizeEvent(self, event):
        width = self.width()
        if width < 600:
            self.clear_btn.setText("🗑 Clear")
            self.download_btn.setText("↓ Download")
        else:
            self.clear_btn.setText("Clear All")
            self.download_btn.setText("Start Download")
        
        base_size = max(10, min(14, int(width / 80)))
        self.setStyleSheet(f"* {{ font-size: {base_size}px; }} QPushButton {{ min-width: {base_size * 8}px; }}")
        super().resizeEvent(event)

    def toggle_resolution(self):
        enabled = self.format_group.checkedButton().property('format') == 'mp4'
        self.resolution_combo.setEnabled(enabled)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.download_path = directory
            self.path_input.setText(directory)

    def clear_fields(self):
        self.url_input.clear()
        self.platform_combo.setCurrentIndex(0)
        self.format_group.buttons()[0].setChecked(True)
        self.resolution_combo.setCurrentIndex(0)
        self.path_input.clear()
        self.status_output.clear()
        self.toggle_resolution()

    def validate_inputs(self):
        if not self.url_input.text().strip():
            QMessageBox.critical(self, "Error", "Please enter a valid URL!")
            return False
        if not self.path_input.text().strip():
            QMessageBox.critical(self, "Error", "Please select a download directory!")
            return False
        if self.format_group.checkedButton().property('format') == 'mp4':
            ffmpeg_path = get_ffmpeg_path()
            if not os.path.isfile(ffmpeg_path):
                QMessageBox.critical(self, "Error", "FFmpeg not found. Required for video processing!")
                return False
        return True

    def start_download(self):
        if not self.validate_inputs():
            return

        self.download_btn.setEnabled(False)
        self.worker = DownloadWorker(
            self.url_input.text(),
            self.platform_combo.currentText(),
            self.format_group.checkedButton().property('format'),
            self.resolution_combo.currentText(),
            self.path_input.text(),
            get_ffmpeg_path()
        )
        self.worker.signals.update_progress.connect(self.update_status)
        self.worker.signals.download_complete.connect(self.download_complete)
        self.worker.signals.error_occurred.connect(self.handle_error)
        
        self.download_thread = threading.Thread(target=self.worker.run)
        self.download_thread.start()

    def update_status(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_output.append(f"[{timestamp}] {message}")
        self.status_output.ensureCursorVisible()

    def download_complete(self):
        self.download_btn.setEnabled(True)
        QMessageBox.information(self, "Success", "Download completed successfully!")
        self.open_download_directory()

    def handle_error(self, message):
        self.download_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", message)

    def open_download_directory(self):
        path = self.path_input.text()
        if os.path.isdir(path):
            try:
                os.startfile(path)
            except AttributeError:
                self.update_status(f"Download directory: {path}")