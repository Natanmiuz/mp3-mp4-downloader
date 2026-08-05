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
- **MP4 video** with resolution control: 360p, 480p, 720p, 1080p or best available.
- **MP3 audio** extracted at 192 kbps via FFmpeg.
- **Smart platform detection**, or pick a source manually (use *Any Website* as a generic fallback).
- **Real-time progress**: percentage, speed and ETA without freezing the UI (downloads run on a background thread).
- **Portable executable**: single `.exe` build with PyInstaller, no installation required.

## Quick start

### Prerequisites

- **Windows 7 or later**
- **Python 3.13** (only when running from source)
- **FFmpeg** — required for MP3 audio extraction and MP4 video merging

> [!IMPORTANT]
> FFmpeg is **not** bundled with the app. You must download it and place `ffmpeg.exe` in the `binaries/` folder next to the executable or repo root.

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

**Option A — Portable executable**

Download `notnet.exe` from the [Releases](https://github.com/Natanmiuz/mp3-mp4-downloader/releases) page and double-click it.

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

1. Paste a video or audio URL.
2. Choose a **source** (Auto-detect is the default; pick *Any Website* for a generic download — resolution selection is disabled then).
3. Choose a **format**:
   - **Video (MP4)** — optionally set the resolution (360p–1080p or *Best available*).
   - **Audio (MP3)** — 192 kbps, resolution is not applicable.
4. Click **Browse** to pick the destination folder.
5. Click **Download** and watch the progress. When finished, the destination folder opens automatically.

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

Build a portable single-file executable with PyInstaller:

```bash
pip install pyinstaller
pyinstaller notnet.spec
```

The executable is written to `dist/notnet.exe`. For a fully portable build, make sure `binaries/ffmpeg.exe` is present next to the exe (the spec bundles it automatically when it exists).

## Project structure

```text
mp3-mp4-downloader/
├── main.py                  # GUI entry point
├── web_server.py            # HTTP API entry point (testing / automation)
├── cli/
│   └── main_cli.py          # CLI entry point + CLI Downloader
├── app/
│   ├── core/
│   │   └── downloader.py    # Shared download engine (Qt Signals + threads)
│   ├── utils/
│   │   ├── helpers.py       # get_ffmpeg_path(), validate_url()
│   │   └── styles.py        # GUI stylesheet (QSS)
│   └── views/
│       └── main_window.py   # Main window (validation, UI, worker threads)
├── binaries/                # ffmpeg.exe (required at runtime, gitignored)
├── notnet.spec              # PyInstaller spec
├── requirements.txt         # Pinned dependencies
└── descargas/               # CLI default output folder (gitignored)
```

## Troubleshooting

**FFmpeg not found (MP4 download fails)**

The GUI validates that `ffmpeg.exe` exists before starting an MP4 download. Place it in `binaries/`, or pass an explicit path in the CLI with `--ffmpeg`.

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
