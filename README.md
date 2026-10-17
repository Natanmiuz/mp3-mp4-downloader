<div align="center">

# NOTNET — Multi-Platform Media Downloader

**A Windows desktop app to download videos and audio from YouTube, Facebook, TikTok, Twitter, Instagram and hundreds of other sites**, powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp).

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white)
![GUI](https://img.shields.io/badge/UI-PySide6-41CD52?style=flat-square&logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-31A053?style=flat-square)

[Overview](#overview) • [Features](#features) • [Quick start](#quick-start) • [Usage](#usage) • [HTTP API](#http-api) • [Build from source](#build-from-source) • [Project structure](#project-structure) • [Troubleshooting](#troubleshooting)

</div>

## Overview

Paste a link, pick a format, and hit download. NOTNET handles the rest — extracting the best available stream and saving it as **MP4 video** or **MP3 audio** (192 kbps).

It ships with three surfaces for the same core engine:

- **GUI** — a modern dark PySide6 desktop app with live progress (percent, speed, ETA) and a detail log.
- **CLI** — a scriptable command-line interface for automation.
- **HTTP API** — a minimal local server for integration and automated testing.

## Features

- **Multi-platform**: works with YouTube, Facebook, TikTok, Twitter, Instagram and virtually any site supported by yt-dlp.
- **MP4 video** with resolution control: 360p, 480p, 720p, 1080p or best available. Output is always an `.mp4` file.
- **MP3 audio** extracted at 192 kbps via FFmpeg.
- **Smart platform detection**: YouTube, TikTok, Instagram, Facebook and X links are recognized as you paste them. Any other site is tried as a generic download, and links pasted without `https://` are completed for you.
- **Real-time progress**: stage, percentage, speed and ETA without freezing the UI (downloads run on a background thread).
- **Cancel anytime** with the Cancel button or <kbd>Esc</kbd>. Partial files are removed.
- **Remembers your choices**: folder, format and quality are kept between sessions. The default folder is your Downloads folder.
- **Portable build**: unzip and run, no installation required. FFmpeg is included and the app opens in under a second.
- **Parallel downloads** of HLS/DASH fragments (4 at a time), which speeds up sites such as X, Instagram and Facebook.

## Quick start

### Prerequisites

- **Windows 7 or later**
- **Python 3.13** (only when running from source)
- **FFmpeg** — required for MP3 audio extraction and MP4 video merging

> [!IMPORTANT]
> The release zip already includes FFmpeg. FFmpeg is **not** stored in this repository, so to run from source or build the app yourself, download it and place `ffmpeg.exe` in the `binaries/` folder at the repo root.

### 1. Get FFmpeg

1. Download a Windows build from [ffmpeg.org](https://ffmpeg.org/download.html) (a static "release essentials" build is fine).
2. Extract the archive and copy `ffmpeg.exe` into the `binaries/` folder:

```text
binaries/
└── ffmpeg.exe
```

3. Verify it works:

```powershell
binaries\ffmpeg.exe -version
```

### 2. Run the app

**Option A — Portable build**

Download `notnet-<version>-win64.zip` from the [Releases](https://github.com/Natanmiuz/mp3-mp4-downloader/releases) page, extract it anywhere, and run `notnet\notnet.exe`. Keep the `_internal` folder next to the exe, because it holds Qt, Python and FFmpeg. Third-party licenses are listed in `THIRD_PARTY_NOTICES.md` inside the folder.

**Option B — From source**

```bash
git clone https://github.com/Natanmiuz/mp3-mp4-downloader.git
cd mp3-mp4-downloader

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

# Launch the GUI
python main.py
```

> [!NOTE]
> The CLI prints progress in **Spanish**, while the GUI uses **English** — this is intentional and matches each surface.

## Usage

### GUI

1. Paste a video or audio link. The line below the field confirms the detected platform, or tells you if the text isn't a link.
2. Choose a **format**:
   - **Video (MP4)**: optionally set the quality (*Best available* or 1080p–360p).
   - **Audio (MP3)**: 192 kbps. Quality is not applicable.
3. Check **Save to** (your Downloads folder by default) or click **Browse…** to change it.
4. Click **Download** or press <kbd>Enter</kbd> and follow the progress. Press **Cancel** or <kbd>Esc</kbd> to stop.
5. When it finishes, click **Show in folder** to open the file's location. If something fails, the panel explains why in plain language and **Details** shows the full log.

### CLI

```bash
python cli/main_cli.py <URL> [OPTIONS]
```

| Option | Description | Default |
|---|---|---|
| `<URL>` | Video or audio URL (optional; interactive prompt if omitted) | — |
| `-f, --format <mp3\|mp4>` | Output format | `mp4` |
| `-o, --output <PATH>` | Output directory | `./descargas` |
| `--ffmpeg <PATH>` | Path to the FFmpeg executable | `ffmpeg` (PATH lookup) |
| `--help` | Show help | — |

```bash
# Download video as MP4 (default)
python cli/main_cli.py "https://www.youtube.com/watch?v=..."

# Extract audio as MP3
python cli/main_cli.py "https://www.youtube.com/watch?v=..." -f mp3

# Custom output folder and FFmpeg path
python cli/main_cli.py "https://www.youtube.com/watch?v=..." -o "D:\downloads" --ffmpeg "C:\ffmpeg\bin\ffmpeg.exe"
```

## HTTP API

A minimal JSON server for automation and testing. It reuses the same download engine as the CLI.

```bash
python web_server.py [PORT]        # defaults to 8000, binds 127.0.0.1
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check → `{"status": "ok"}` |
| `GET` | `/` | Lists available endpoints |
| `POST` | `/download` | Download a URL (`url`, `format`, optional `path` in JSON body) |

```bash
curl -X POST http://127.0.0.1:8000/download \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=...", "format": "mp4"}'
```

## Requirements

- **OS**: Windows 7 or later
- **Python**: 3.13 (source builds only)
- **FFmpeg**: see [Quick start](#quick-start)
- **Dependencies**: listed in `requirements.txt` — `PySide6 6.11`, `yt-dlp` (pinned), `shiboken6`

> [!TIP]
> Platform changes (e.g. YouTube breaking changes) outpace older releases. If downloads start failing, upgrade yt-dlp first:
> `pip install --upgrade yt-dlp`

## Build from source

Build the portable folder with PyInstaller, running it from the repo root:

```bash
pip install pyinstaller
pyinstaller notnet.spec
```

The build writes `dist/notnet/` (`notnet.exe` plus `_internal/`) and the release asset `dist/notnet-<version>-win64.zip`. Upload the zip to GitHub Releases; build output and FFmpeg never go into the repository. The spec:

- builds a folder instead of a single `.exe`. A one-file build would unpack about 370 MB (mostly FFmpeg) to `%TEMP%` on every launch, which took 8–10 s. The folder build opens in under a second.
- requires `binaries/ffmpeg.exe` and bundles everything in `binaries/` into `_internal/binaries`. The build stops if FFmpeg is missing, or if the FFmpeg binary was built as `nonfree` (not redistributable).
- leaves out the Qt modules the app doesn't use (OpenGL software renderer, Quick/QML, PDF, SVG, network, image-format plugins, translations).
- generates the app icon, the Windows version info (from `__version__` in `app/__init__.py`) and `THIRD_PARTY_NOTICES.md` with a `licenses/` folder (FFmpeg, Qt/PySide6, Python and each bundled package), all through `tools/build_assets.py`.
- enables Python UTF-8 mode and disables UPX compression, which reduces antivirus false positives.

### Code signing (optional, manual)

Unsigned executables trigger SmartScreen warnings. If you have a code-signing certificate, sign and timestamp the exe after building:

```powershell
signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 dist\notnet\notnet.exe
signtool verify /pa /v dist\notnet\notnet.exe
```

Sign before uploading, then recreate the zip, because the spec zips the folder at the end of the build.

Always include an RFC 3161 timestamp (`/tr`). Without it, the signature stops being valid when the certificate expires.

## Project structure

```text
mp3-mp4-downloader/
├── main.py                  # GUI entry point
├── web_server.py            # HTTP API entry point (testing / automation)
├── cli/
│   └── main_cli.py          # CLI entry point + CLI Downloader
├── app/
│   ├── core/
│   │   └── downloader.py    # GUI download worker (QObject on a QThread, cancellable)
│   ├── utils/
│   │   ├── helpers.py       # ffmpeg path, URL checks, platform detection, error hints
│   │   └── styles.py        # Colour + type tokens, QSS, app icon
│   └── views/
│       └── main_window.py   # Main window (form, progress panel, settings)
├── binaries/                # ffmpeg.exe (required at runtime, gitignored)
├── tools/
│   └── build_assets.py      # Icon, version resource and third-party notices for the spec
├── licenses/                # GPL-3.0 / LGPL-3.0 texts shipped with the build
├── notnet.spec              # PyInstaller spec
├── requirements.txt         # Pinned dependencies
└── descargas/               # CLI default output folder (gitignored)
```

## Troubleshooting

**FFmpeg not found**

The GUI checks that `ffmpeg.exe` exists before starting any download, since MP4 merging and MP3 extraction both need it. Place it in `binaries/`, or pass an explicit path in the CLI with `--ffmpeg`.

**Download fails mid-way**

- Check your internet connection and that the URL is public.
- Make sure there is enough free disk space.
- Upgrade yt-dlp, as platforms frequently change: `pip install --upgrade yt-dlp`.
- Re-check FFmpeg — MP3 extraction and MP4 merging both need it.

**Something else**

Open an [issue](https://github.com/Natanmiuz/mp3-mp4-downloader/issues) with the download URL, format and the output of the **Details** log panel (GUI) or the console output (CLI).

## Legal notice

> [!WARNING]
> This software is provided for **personal, non-commercial use only**. You are responsible for respecting the terms of service and copyright laws of each platform, and for obtaining proper permission before downloading content. Downloading DRM-protected or access-controlled content is not supported and is your responsibility to avoid.
