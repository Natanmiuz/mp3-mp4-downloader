import os
import sys

def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        return os.path.join(base_path, 'binaries', 'ffmpeg.exe')
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, 'binaries', 'ffmpeg.exe')

def validate_url(url):
    valid_protocols = ('http://', 'https://', 'ftp://')
    return url.strip() != "" and any(url.startswith(proto) for proto in valid_protocols)