import os
from datetime import datetime
from PySide6.QtCore import QObject, Signal
import yt_dlp

class DownloadSignals(QObject):
    update_progress = Signal(str)
    download_complete = Signal()
    error_occurred = Signal(str)

class DownloadWorker:
    def __init__(self, url, platform, format, resolution, path, ffmpeg_path):
        self.url = url
        self.platform = platform
        self.format = format
        self.resolution = resolution
        self.path = path
        self.ffmpeg_path = ffmpeg_path
        self.signals = DownloadSignals()

    def run(self):
        try:
            options = self.build_options()
            
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([self.url])
                
            self.signals.download_complete.emit()
        except Exception as e:
            self.signals.error_occurred.emit(str(e))

    def build_options(self):
        options = {
            'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
            'ffmpeg_location': self.ffmpeg_path,
            'progress_hooks': [self.progress_hook],
            'noplaylist': True,
            'quiet': True,
            'no_warnings': False,
        }

        if self.format == 'mp3':
            options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            options['format'] = self.get_video_format()

        return options

    def get_video_format(self):
        if self.resolution == 'Best available':
            return 'bestvideo+bestaudio/best'
        height = int(self.resolution.replace('p', ''))
        return f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A').strip()
            speed = d.get('_speed_str', 'N/A').strip()
            self.signals.update_progress.emit(f"Progress: {percent} | Speed: {speed}")
        elif d['status'] == 'finished':
            self.signals.update_progress.emit("Post-processing...")