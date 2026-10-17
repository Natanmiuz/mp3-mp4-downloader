import gc
import glob
import os
import threading
import time
from PySide6.QtCore import QObject, Signal, Slot

# Parallel fragment downloads for HLS/DASH sources (X, Instagram, Facebook...).
CONCURRENT_FRAGMENTS = 4

POSTPROCESSOR_STAGES = {
    'Merger': "Merging video and audio…",
    'ExtractAudio': "Converting to MP3…",
}


class _YtdlLogger:
    """Routes yt-dlp's screen output into the GUI log instead of the console."""

    def __init__(self, append):
        self._append = append

    def debug(self, message):
        if not message.startswith('[debug] '):
            self._append(message)

    def info(self, message):
        self._append(message)

    def warning(self, message):
        self._append(f"Warning: {message}")

    def error(self, message):
        self._append(message)


class DownloadWorker(QObject):
    """Runs one yt-dlp download. Move it to a QThread, then connect `run` to
    QThread.started. Only the terminal signals below are emitted, from that thread.

    With concurrent fragments, yt-dlp calls the hooks from its own pool threads,
    so the hooks never emit Qt signals: they write into a lock-protected state
    that the GUI reads with snapshot() on a timer.
    """

    succeeded = Signal(str)  # final file path, '' if yt-dlp didn't report one
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, url, format, resolution, path, ffmpeg_path, cancel_event):
        super().__init__()
        self.url = url
        self.format = format
        self.resolution = resolution
        self.path = path
        self.ffmpeg_path = ffmpeg_path
        self._cancel_event = cancel_event
        self._lock = threading.Lock()
        self._state = {'stage': '', 'title': '', 'percent': -1.0, 'speed': '', 'eta': ''}
        self._log = []
        self._final_path = ''
        self._written_files = set()

    def snapshot(self):
        """Thread-safe copy of the progress state plus the log lines added since
        the previous call. percent is -1.0 while the total is unknown."""
        with self._lock:
            state = dict(self._state)
            state['log'], self._log = self._log, []
        return state

    @Slot()
    def run(self):
        self._update(stage="Fetching media info…", percent=-1.0)
        error = None
        try:
            # Imported here, not at module level: yt-dlp takes ~0.5 s to import,
            # which would otherwise delay the window on every launch.
            import yt_dlp
            with yt_dlp.YoutubeDL(self.build_options()) as ydl:
                ydl.download([self.url])
        except Exception as e:
            error = str(e)

        # Hooks only raise DownloadCancelled once the event is set; any other
        # error that lands after a cancel request is reported as a cancel too.
        if self._cancel_event.is_set() and error is not None:
            # Cleanup runs outside the except block: the traceback's frames keep
            # yt-dlp's file handles open, and Windows can't delete open files.
            self._remove_partial_files()
            self.cancelled.emit()
        elif error is not None:
            self.failed.emit(error)
        else:
            self.succeeded.emit(self._final_path)

    def build_options(self):
        options = {
            'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
            'ffmpeg_location': self.ffmpeg_path,
            'progress_hooks': [self.progress_hook],
            'postprocessor_hooks': [self.postprocessor_hook],
            'post_hooks': [self.post_hook],
            'logger': _YtdlLogger(self._append_log),
            'noprogress': True,
            'color': 'no_color',
            'noplaylist': True,
            'concurrent_fragment_downloads': CONCURRENT_FRAGMENTS,
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
            options.update({
                'format': self.get_video_format(),
                # Prefer H.264/AAC streams and always merge into an .mp4 container;
                # otherwise YouTube's VP9/Opus streams end up as .webm or .mkv.
                'format_sort': ['res', 'ext:mp4:m4a'],
                'merge_output_format': 'mp4',
            })

        return options

    def get_video_format(self):
        if self.resolution == 'Best available':
            return 'bestvideo+bestaudio/best'
        height = int(self.resolution.replace('p', ''))
        # Trailing /best keeps sites without height metadata downloadable.
        return f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'

    # yt-dlp hooks: may run on yt-dlp's fragment threads, never emit signals here.

    def progress_hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            with self._lock:
                self._written_files.update(d[key] for key in ('filename', 'tmpfilename') if d.get(key))
        self._raise_if_cancelled()

        info = d.get('info_dict') or {}
        fields = {'title': info['title']} if info.get('title') else {}
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes') or 0
            fields.update(
                stage=self._download_stage(info),
                percent=(downloaded / total * 100) if total else -1.0,
                speed=(d.get('_speed_str') or '').strip(),
                eta=(d.get('_eta_str') or '').strip(),
            )
        elif status == 'finished':
            fields.update(percent=100.0, speed='', eta='')
        self._update(**fields)

    def postprocessor_hook(self, d):
        if d.get('status') != 'started':
            return
        self._raise_if_cancelled()
        stage = POSTPROCESSOR_STAGES.get(d.get('postprocessor'))
        if stage:
            self._update(stage=stage, percent=-1.0, speed='', eta='')

    def post_hook(self, filepath):
        self._final_path = filepath

    def _raise_if_cancelled(self):
        if self._cancel_event.is_set():
            from yt_dlp.utils import DownloadCancelled
            raise DownloadCancelled()

    def _update(self, **fields):
        with self._lock:
            self._state.update(fields)

    def _append_log(self, message):
        with self._lock:
            self._log.append(message)

    def _download_stage(self, info):
        if self.format == 'mp3':
            return "Downloading audio…"
        has_video = info.get('vcodec') not in (None, 'none')
        has_audio = info.get('acodec') not in (None, 'none')
        if has_video and not has_audio:
            return "Downloading video stream…"
        if has_audio and not has_video:
            return "Downloading audio stream…"
        return "Downloading…"

    def _remove_partial_files(self):
        # Only files this run was writing; anything yt-dlp skipped as
        # "already downloaded" never reaches the 'downloading' status.
        with self._lock:
            written = set(self._written_files)
        candidates = set()
        for path in written:
            candidates.update({path, path + '.ytdl'})
            candidates.update(glob.glob(glob.escape(path) + '.part*'))
            candidates.update(glob.glob(glob.escape(path) + '-Frag*'))
        gc.collect()  # close file objects still held by reference cycles
        for _ in range(5):
            remaining = set()
            for path in candidates:
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                except PermissionError:
                    remaining.add(path)  # still open (fragment thread or antivirus)
                except OSError:
                    pass
            if not remaining:
                break
            candidates = remaining
            time.sleep(0.2)
