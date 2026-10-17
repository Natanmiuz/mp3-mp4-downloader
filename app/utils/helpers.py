import os
import re
import sys
from urllib.parse import urlparse

PLATFORM_HOSTS = {
    'YouTube': ('youtube.com', 'youtu.be', 'youtube-nocookie.com'),
    'TikTok': ('tiktok.com',),
    'Instagram': ('instagram.com',),
    'Facebook': ('facebook.com', 'fb.watch', 'fb.com'),
    'X (Twitter)': ('twitter.com', 'x.com'),
}

# (pattern, plain-language explanation) checked in order against yt-dlp errors.
ERROR_HINTS = [
    (r"ffmpeg is not installed|ffmpeg not found",
     "FFmpeg was not found. Put ffmpeg.exe in the binaries folder next to the app."),
    (r"Unsupported URL", "This link isn't supported. Check that it points to a video or audio page."),
    (r"not a bot|Sign in to confirm", "The site asked to confirm you're not a bot. Try again later or update yt-dlp."),
    (r"Private video|login required|requires authentication|This video is private",
     "This media is private or needs you to sign in."),
    (r"Video unavailable|not available in your country|has been removed", "This media is unavailable."),
    (r"Requested format is not available", "That quality isn't available here. Try \"Best available\"."),
    (r"HTTP Error 403", "The site refused the download (HTTP 403). Updating yt-dlp usually fixes this."),
    (r"getaddrinfo|Failed to resolve|timed out|Unable to download webpage|Connection (refused|reset|aborted)",
     "Couldn't reach the site. Check your internet connection."),
]


def get_ffmpeg_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        candidates = [
            os.path.join(base_path, 'binaries', 'ffmpeg.exe'),
            os.path.join(base_path, 'ffmpeg.exe'),
        ]
        for candidate in candidates:
            if os.path.isfile(candidate):
                return candidate
        return candidates[0]
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        return os.path.join(project_root, 'binaries', 'ffmpeg.exe')


def normalize_url(url):
    """Adds https:// to bare links such as 'youtube.com/watch?v=…'."""
    url = url.strip()
    if '://' not in url and re.match(r'^[\w-]+(\.[\w-]+)+(:\d+)?([/?#]|$)', url):
        return 'https://' + url
    return url


def validate_url(url):
    parsed = urlparse(url.strip())
    return parsed.scheme in ('http', 'https', 'ftp') and bool(parsed.netloc)


def detect_platform(url):
    """Returns a known platform name for the URL's host, or None."""
    host = (urlparse(url.strip()).hostname or '').lower()
    for name, domains in PLATFORM_HOSTS.items():
        if any(host == domain or host.endswith('.' + domain) for domain in domains):
            return name
    return None


def describe_error(message):
    """Turns a raw yt-dlp error into one plain-language sentence."""
    for pattern, hint in ERROR_HINTS:
        if re.search(pattern, message, re.IGNORECASE):
            return hint
    first_line = message.strip().splitlines()[0] if message.strip() else "Unknown error."
    first_line = re.sub(r'^ERROR:\s*', '', first_line)
    return first_line if len(first_line) <= 140 else first_line[:137] + "…"
