import os
import re
import subprocess
import sys
import threading
from datetime import datetime
from PySide6.QtCore import Qt, QSize, QSettings, QStandardPaths, QThread, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QComboBox, QFrame, QPushButton, QTextEdit, QFileDialog,
    QMessageBox, QButtonGroup, QSizePolicy, QProgressBar, QStackedWidget
)
from app.core.downloader import DownloadWorker
from app.utils.helpers import describe_error, detect_platform, get_ffmpeg_path, normalize_url, validate_url
from app.utils.styles import build_app_icon

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


class VideoDownloader(QMainWindow):
    RESOLUTIONS = ['Best available', '1080p', '720p', '480p', '360p']

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NOTNET")
        self.setMinimumSize(QSize(460, 520))
        self.resize(QSize(560, 600))
        self.settings = QSettings()
        self._thread = None
        self._worker = None
        self._cancel_event = threading.Event()
        self._close_requested = False
        self._shown = {}
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self.poll_progress)
        self._active_dir = ""
        self._final_path = ""
        self.setup_ui()
        self.setup_signals()
        self.load_settings()
        self.update_format_controls()
        self.update_url_hint()
        self.update_ready_state()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root = QVBoxLayout(central_widget)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)
        brand_icon = QLabel()
        brand_icon.setPixmap(build_app_icon().pixmap(QSize(24, 24)))
        title = QLabel("NOTNET")
        title.setObjectName("appTitle")
        subtitle = QLabel("Media downloader")
        subtitle.setObjectName("appSubtitle")
        header.addWidget(brand_icon)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(subtitle)
        root.addLayout(header)
        root.addSpacing(14)

        # Link
        root.addWidget(self.section_label("LINK"))
        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlField")
        self.url_input.setPlaceholderText("Paste a video or audio link…")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.setAccessibleName("Media link")
        root.addWidget(self.url_input)
        self.url_hint = QLabel()
        self.url_hint.setObjectName("urlHint")
        self.url_hint.setWordWrap(True)
        root.addWidget(self.url_hint)
        root.addSpacing(10)

        # Format / Quality: quality depends on format, so it sits to the right of it
        options = QGridLayout()
        options.setHorizontalSpacing(16)
        options.setVerticalSpacing(8)
        options.setColumnStretch(0, 1)
        options.setColumnStretch(1, 1)

        seg_frame = QFrame()
        seg_frame.setObjectName("segmented")
        seg_layout = QHBoxLayout(seg_frame)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(3)
        self.format_group = QButtonGroup(self)
        self.video_btn = QPushButton("▶  Video")
        self.video_btn.setProperty("format", "mp4")
        self.video_btn.setToolTip("MP4 video")
        self.audio_btn = QPushButton("♪  Audio")
        self.audio_btn.setProperty("format", "mp3")
        self.audio_btn.setToolTip("MP3 audio")
        for button in (self.video_btn, self.audio_btn):
            button.setCheckable(True)
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self.prepare_button(button)
            seg_layout.addWidget(button)
            self.format_group.addButton(button)
        self.video_btn.setChecked(True)
        options.addWidget(self.section_label("FORMAT"), 0, 0)
        options.addWidget(seg_frame, 1, 0)

        self.quality_stack = QStackedWidget()
        self.res_combo = QComboBox()
        self.res_combo.addItems(self.RESOLUTIONS)
        self.res_combo.setAccessibleName("Video quality")
        self.audio_note = QLabel("MP3 · 192 kbps")
        self.audio_note.setObjectName("audioNote")
        self.quality_stack.addWidget(self.res_combo)
        self.quality_stack.addWidget(self.audio_note)
        options.addWidget(self.section_label("QUALITY"), 0, 1)
        options.addWidget(self.quality_stack, 1, 1)
        root.addLayout(options)
        root.addSpacing(10)

        # Save to
        root.addWidget(self.section_label("SAVE TO"))
        path_row = QHBoxLayout()
        path_row.setSpacing(10)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        self.path_input.setPlaceholderText("Choose a folder…")
        self.path_input.setAccessibleName("Download folder")
        self.browse_btn = QPushButton("Browse…")
        self.prepare_button(self.browse_btn)
        path_row.addWidget(self.path_input, 1)
        path_row.addWidget(self.browse_btn)
        root.addLayout(path_row)
        root.addSpacing(18)

        # Actions
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear the link and the last result")
        self.download_btn = QPushButton("Download")
        self.download_btn.setProperty("variant", "primary")
        self.download_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for button in (self.clear_btn, self.download_btn):
            self.prepare_button(button)
        actions.addWidget(self.clear_btn)
        actions.addWidget(self.download_btn, 2)
        root.addLayout(actions)
        root.addSpacing(10)

        # Progress panel
        panel = QFrame()
        panel.setObjectName("progressPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 14, 18, 14)
        panel_layout.setSpacing(8)

        top = QHBoxLayout()
        self.stage_label = QLabel()
        self.stage_label.setObjectName("stageLabel")
        self.percent_label = QLabel("0%")
        self.percent_label.setObjectName("percentLabel")
        top.addWidget(self.stage_label, 1, Qt.AlignBottom)
        top.addWidget(self.percent_label, 0, Qt.AlignBottom)

        self.media_title = QLabel()
        self.media_title.setObjectName("mediaTitle")
        self.media_title.setWordWrap(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAccessibleName("Download progress")

        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        self.info_label = QLabel()
        self.info_label.setObjectName("infoLabel")
        self.info_label.setWordWrap(True)
        self.info_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setToolTip("Stop the download (Esc)")
        self.open_folder_btn = QPushButton("Show in folder")
        self.details_btn = QPushButton("Details ▾")
        self.details_btn.setProperty("variant", "link")
        self.details_btn.setCheckable(True)
        for button in (self.cancel_btn, self.open_folder_btn, self.details_btn):
            self.prepare_button(button)
        bottom.addWidget(self.info_label, 1)
        bottom.addWidget(self.cancel_btn, 0, Qt.AlignTop)
        bottom.addWidget(self.open_folder_btn, 0, Qt.AlignTop)
        bottom.addWidget(self.details_btn, 0, Qt.AlignTop)

        self.log_output = QTextEdit()
        self.log_output.setObjectName("logOutput")
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(110)
        self.log_output.setMaximumHeight(170)
        self.log_output.setAccessibleName("Download log")
        self.log_output.hide()

        panel_layout.addLayout(top)
        panel_layout.addWidget(self.media_title)
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

    def prepare_button(self, button):
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        # Tab-only focus: the focus ring shows for keyboard users, not after clicks.
        button.setFocusPolicy(Qt.FocusPolicy.TabFocus)

    def setup_signals(self):
        self.url_input.textChanged.connect(self.update_url_hint)
        self.url_input.textChanged.connect(self.update_ready_state)
        self.url_input.returnPressed.connect(self.start_download)
        self.path_input.textChanged.connect(self.update_ready_state)
        self.format_group.buttonClicked.connect(self.on_format_clicked)
        self.res_combo.currentTextChanged.connect(lambda text: self.settings.setValue("quality", text))
        self.browse_btn.clicked.connect(self.browse_directory)
        self.clear_btn.clicked.connect(self.clear_fields)
        self.download_btn.clicked.connect(self.start_download)
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.open_folder_btn.clicked.connect(self.show_in_folder)
        self.details_btn.toggled.connect(self.set_details_visible)
        cancel_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        cancel_shortcut.activated.connect(self.cancel_download)

    # Settings

    def load_settings(self):
        folder = self.settings.value("download_dir", "", type=str)
        if not folder or not os.path.isdir(folder):
            folder = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
        self.set_download_dir(folder)
        if self.settings.value("format", "mp4", type=str) == "mp3":
            self.audio_btn.setChecked(True)
        index = self.res_combo.findText(self.settings.value("quality", "Best available", type=str))
        if index >= 0:
            self.res_combo.setCurrentIndex(index)

    def set_download_dir(self, folder):
        folder = os.path.normpath(folder)
        self.path_input.setText(folder)
        self.path_input.setToolTip(folder)
        self.path_input.setCursorPosition(0)

    # Form state

    def current_format(self):
        return self.format_group.checkedButton().property("format")

    def on_format_clicked(self):
        self.settings.setValue("format", self.current_format())
        self.update_format_controls()

    def update_format_controls(self):
        self.quality_stack.setCurrentIndex(0 if self.current_format() == "mp4" else 1)

    def update_url_hint(self):
        text = normalize_url(self.url_input.text())
        if not text:
            state, message = "", "Works with YouTube, TikTok, Instagram, Facebook, X and many more sites."
        elif not validate_url(text):
            state, message = "error", "This doesn't look like a link. Copy it from your browser's address bar."
        else:
            platform = detect_platform(text)
            if platform:
                state, message = "detected", f"✓ {platform} link"
            else:
                state, message = "", "Website link: NOTNET will look for media on the page."
        self.url_hint.setText(message)
        self.set_state(state, self.url_hint)

    def update_ready_state(self):
        if self._thread is not None:
            return
        ready = validate_url(normalize_url(self.url_input.text())) and bool(self.path_input.text().strip())
        self.download_btn.setEnabled(ready)

    def set_form_enabled(self, enabled):
        for widget in (self.url_input, self.video_btn, self.audio_btn, self.res_combo,
                       self.browse_btn, self.clear_btn):
            widget.setEnabled(enabled)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Folder", self.path_input.text())
        if directory:
            self.set_download_dir(directory)
            self.settings.setValue("download_dir", directory)

    def clear_fields(self):
        self.url_input.clear()
        self.log_output.clear()
        self.progress_panel.hide()
        self.url_input.setFocus()

    def validate_inputs(self):
        folder = self.path_input.text()
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Folder not found",
                                f"This folder doesn't exist anymore:\n{folder}\n\nChoose another one with Browse.")
            return False
        ffmpeg_path = get_ffmpeg_path()
        if not os.path.isfile(ffmpeg_path):
            kind = "MP4 video" if self.current_format() == "mp4" else "MP3 audio"
            QMessageBox.critical(self, "FFmpeg not found",
                                 f"NOTNET needs FFmpeg to save {kind}.\n\nPut ffmpeg.exe here:\n{ffmpeg_path}")
            return False
        return True

    # Download lifecycle

    def start_download(self):
        if self._thread is not None or not self.download_btn.isEnabled():
            return
        if not self.validate_inputs():
            return

        self._active_dir = self.path_input.text()
        self._final_path = ""
        self._cancel_event = threading.Event()
        self.reset_progress()
        self.set_running(True)

        self._thread = QThread(self)
        # The worker can't have a parent across threads; self._worker keeps it alive.
        self._worker = worker = DownloadWorker(
            normalize_url(self.url_input.text()),
            self.current_format(),
            self.res_combo.currentText(),
            self._active_dir,
            get_ffmpeg_path(),
            self._cancel_event,
        )
        # Move first, connect second, so AutoConnection queues slots onto the GUI thread.
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.succeeded.connect(self.on_succeeded)
        worker.failed.connect(self.on_failed)
        worker.cancelled.connect(self.on_cancelled)
        for signal in (worker.succeeded, worker.failed, worker.cancelled):
            signal.connect(self._thread.quit)
        self._thread.finished.connect(worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self.on_thread_finished)
        self._thread.start()
        self._shown = {}
        self._poll_timer.start()

    def poll_progress(self):
        """Applies the worker's latest progress. Polling instead of per-hook
        signals keeps Qt calls off yt-dlp's fragment threads and caps UI updates
        at the timer rate."""
        if self._worker is None:
            return
        state = self._worker.snapshot()
        for line in state.pop("log"):
            self.append_log(line)
        if state == self._shown:
            return
        previous, self._shown = self._shown, state
        if state["title"] and state["title"] != previous.get("title"):
            self.on_title(state["title"])
        if self._cancel_event.is_set():
            return  # keep "Cancelling…" on screen
        if state["stage"] != previous.get("stage"):
            self.stage_label.setText(state["stage"])
        self.on_progress(state["percent"], state["speed"], state["eta"])

    def stop_polling(self):
        self.poll_progress()  # flush the final state and log lines
        self._poll_timer.stop()

    def cancel_download(self):
        if self._thread is None or self._cancel_event.is_set():
            return
        self._cancel_event.set()
        self.cancel_btn.setEnabled(False)
        self.stage_label.setText("Cancelling…")
        self.info_label.setText("Stopping after the current step…")

    def on_thread_finished(self):
        self._thread = None
        self._worker = None
        self.update_ready_state()
        if self._close_requested:
            self.close()

    def set_running(self, running):
        if running:
            # Park focus on the panel; otherwise disabling the URL field hands
            # it to the read-only path field, which selects its text.
            self.progress_panel.setFocus()
        self.set_form_enabled(not running)
        self.download_btn.setEnabled(not running)
        self.download_btn.setText("Downloading…" if running else "Download")
        self.cancel_btn.setVisible(running)
        self.cancel_btn.setEnabled(running)
        if not running:
            self.progress_bar.setRange(0, 100)

    def reset_progress(self):
        self.set_state("", self.stage_label, self.percent_label, self.progress_bar, self.info_label)
        self.stage_label.setText("Starting…")
        self.progress_bar.setValue(0)
        self.percent_label.hide()
        self.media_title.clear()
        self.media_title.hide()
        self.info_label.clear()
        self.info_label.setToolTip("")
        self.open_folder_btn.hide()
        self.progress_bar.show()
        self.log_output.clear()
        self.set_details_visible(False)
        self.progress_panel.show()
        self.schedule_fit()

    def on_title(self, title):
        self.media_title.setText(title)
        self.media_title.setToolTip(title)
        self.media_title.show()
        self.schedule_fit()

    def on_progress(self, percent, speed, eta):
        if percent < 0:
            self.progress_bar.setRange(0, 0)  # busy indicator
            self.percent_label.hide()
        else:
            self.progress_bar.setRange(0, 100)
            value = min(100, int(percent))
            self.progress_bar.setValue(value)
            self.percent_label.setText(f"{value}%")
            self.percent_label.show()
        if self._cancel_event.is_set():
            return
        if speed:
            self.info_label.setText(f"{speed} · {eta} left" if eta else speed)
        elif percent < 0:
            self.info_label.clear()

    def on_succeeded(self, path):
        self.stop_polling()
        self._final_path = path
        self.set_running(False)
        self.progress_bar.setValue(100)
        self.percent_label.setText("100%")
        self.percent_label.show()
        self.stage_label.setText("✓ Download complete")
        self.set_state("success", self.stage_label, self.percent_label, self.progress_bar)
        # The title row already names the media; keep this line short.
        folder_path = os.path.dirname(path) if path else self._active_dir
        folder = os.path.basename(os.path.normpath(folder_path)) or folder_path
        extension = os.path.splitext(path)[1].lstrip(".").upper() if path else ""
        self.info_label.setText(f"Saved as {extension} in {folder}" if extension else f"Saved in {folder}")
        self.info_label.setToolTip(path or self._active_dir)
        self.open_folder_btn.show()
        self.open_folder_btn.setFocus()
        QApplication.alert(self)

    def on_failed(self, message):
        self.stop_polling()
        self.set_running(False)
        self.percent_label.hide()
        self.progress_bar.hide()
        self.stage_label.setText("✕ Download failed")
        self.set_state("error", self.stage_label, self.info_label)
        self.info_label.setText(describe_error(ANSI_ESCAPE.sub("", message)))
        self.append_log(message)
        self.set_details_visible(True)
        QApplication.alert(self)

    def on_cancelled(self):
        self.stop_polling()
        self.set_running(False)
        self.percent_label.hide()
        self.progress_bar.hide()
        self.stage_label.setText("Download cancelled")
        self.info_label.setText("Partial files were removed.")

    def closeEvent(self, event):
        if self._thread is not None:
            if not self._close_requested:
                answer = QMessageBox.question(
                    self, "Download in progress",
                    "A download is still running. Cancel it and close NOTNET?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if answer != QMessageBox.Yes:
                    event.ignore()
                    return
                self._close_requested = True
                self.cancel_download()
            # on_thread_finished closes the window once the worker has stopped.
            event.ignore()
            return
        super().closeEvent(event)

    # Panel helpers

    def set_details_visible(self, visible):
        self.details_btn.blockSignals(True)
        self.details_btn.setChecked(visible)
        self.details_btn.blockSignals(False)
        self.details_btn.setText("Details ▴" if visible else "Details ▾")
        self.log_output.setVisible(visible)
        self.schedule_fit()

    def schedule_fit(self):
        # Wrapped labels report their height only after the layout runs.
        QTimer.singleShot(0, self.fit_to_content)

    def fit_to_content(self):
        """Grows the window when the panel needs more room; never shrinks it."""
        central = self.centralWidget()
        layout = central.layout()
        layout.activate()
        needed = layout.totalHeightForWidth(central.width()) if layout.hasHeightForWidth() \
            else layout.totalSizeHint().height()
        screen = self.screen()
        if screen is not None:
            frame_extra = self.frameGeometry().height() - self.height()
            needed = min(needed, screen.availableGeometry().height() - frame_extra)
        if needed > self.height():
            self.resize(self.width(), needed)

    def append_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {ANSI_ESCAPE.sub('', message)}")
        self.log_output.ensureCursorVisible()

    def set_state(self, state, *widgets):
        for widget in widgets:
            widget.setProperty("state", state)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

    def show_in_folder(self):
        target = self._final_path
        if target and os.path.isfile(target) and sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(target)])
        elif os.path.isdir(self._active_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._active_dir))
