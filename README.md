# NONET: Multi-Platform Media Downloader 🎥🔽

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)  
![License](https://img.shields.io/badge/License-MIT-green)  
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)  
![Status](https://img.shields.io/badge/Status-Active-success)  

**NONET** is a feature-rich graphical tool for downloading videos and audios from YouTube, Facebook, TikTok, Twitter, Instagram, and virtually any website. Simple, intuitive, and powered by `yt_dlp`.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
   - [GUI Mode](#gui-mode)
   - [CLI Mode](#cli-mode)
5. [Requirements](#requirements)
6. [Build from Source](#build-from-source)
7. [Development](#development)
8. [Legal Notice](#legal-notice)

---

## Quick Start

### 1. Prerequisites
- **Windows 7+**
- **Python 3.8+** (for running from source)
- **FFmpeg** (required for audio conversion)

### 2. Get FFmpeg
FFmpeg is required for audio processing and is **not** included in the package.

**Download FFmpeg:**
1. Visit [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. Download the Windows build (full or static version)
3. Extract the folder and place `ffmpeg.exe` in the `binaries/` directory of NONET

**Verify FFmpeg:**
```bash
binaries/ffmpeg.exe -version
```

### 3. Run the Application

**Option A: Executable (Recommended)**
- Download `NONET.exe` from the [releases page](https://github.com/your-username/NONET/releases)
- Double-click to run (no installation required)

**Option B: From Source**
```bash
# Clone or download the repository
git clone https://github.com/your-username/NONET.git
cd NONET

# Install dependencies
pip install -r requirements.txt

# Run the GUI
python main.py

# Or run CLI
python cli/main_cli.py --help
```

---

## Features ✅

- 🎯 **Smart Platform Detection**: Recognizes YouTube, Facebook, TikTok, Twitter, Instagram, and more
- 🌐 **Universal Downloader**: Download from virtually any website with video content
- 📥 **Flexible Output**: MP4 (video) or MP3 (audio) with quality selection
- 🎛️ **Quality Control**: Choose resolution (360p–1080p) or auto-select best available
- 🖥️ **Dual Interface**: Modern GUI or powerful CLI for automation
- 📊 **Real-time Progress**: Track download speed, ETA, and completion percentage
- ✅ **Error Handling**: Clear feedback on download status with success/error notifications
- 🚀 **Portable**: No installation needed—self-contained executable

---

## Installation

### From Executable (Windows)

1. Download the latest `NONET.exe` from [Releases](https://github.com/your-username/NONET/releases)
2. Place `ffmpeg.exe` in a new `binaries/` folder next to the executable
3. Run `NONET.exe`

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/your-username/NONET.git
cd NONET

# Create a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

---

## Usage

### GUI Mode

1. **Paste the URL**
   - Copy and paste the video/audio link into the URL field

2. **Select Platform** (auto-detection available)
   - **Auto-detect**: Automatic recognition
   - **YouTube, Facebook, TikTok, Twitter, Instagram**: Specific platform
   - **Any Website**: Generic downloader for other sources

3. **Choose Format**
   - **MP4**: Video download (you can select quality)
   - **MP3**: Audio-only download (192 kbps)

4. **Select Resolution** (MP4 only)
   - **360p, 480p, 720p, 1080p**: Fixed resolution
   - **Best available**: Highest quality available
   - *(Disabled for "Any Website" option)*

5. **Choose Download Location**
   - Click **Browse...** and select the destination folder

6. **Start Download**
   - Click **Start Download** and monitor progress in real time

### CLI Mode

The CLI provides a command-line interface for automation and scripting.

**Basic Usage:**
```bash
python cli/main_cli.py <URL> [OPTIONS]
```

**Examples:**

```bash
# Download as MP4 (default)
python cli/main_cli.py "https://www.youtube.com/watch?v=example"

# Download as MP3
python cli/main_cli.py "https://www.youtube.com/watch?v=example" -f mp3

# Specify output directory
python cli/main_cli.py "https://www.youtube.com/watch?v=example" -o "./my_downloads"

# Custom FFmpeg path
python cli/main_cli.py "https://www.youtube.com/watch?v=example" --ffmpeg "C:\ffmpeg\ffmpeg.exe"

# Interactive mode (if URL not provided)
python cli/main_cli.py
```

**Available Options:**
```
-f, --format {mp3,mp4}    Output format (default: mp4)
-o, --output PATH         Output directory (default: ./descargas)
--ffmpeg PATH             FFmpeg executable path (default: ffmpeg)
--help                    Show help message
```

---

## Requirements

### System Requirements
- **OS**: Windows 7 or later
- **RAM**: 512 MB minimum
- **Disk Space**: Varies by video quality (100 MB–3 GB per download)

### Software Dependencies
- **Python 3.8+** (if running from source)
- **FFmpeg** (required for audio/video processing)

### Python Packages
Listed in `requirements.txt`:
- `PySide6`: GUI framework
- `yt_dlp`: Core downloader engine

---

## Build from Source

### Create Executable (PyInstaller)

```bash
# Install PyInstaller
pip install pyinstaller

# Build the executable
pyinstaller NONET.spec

# The executable will be in the dist/ folder
```

**Note:** Make sure `binaries/ffmpeg.exe` is included in the distribution for a fully portable executable.

---

## Development

### Project Structure
```
NONET/
├── main.py                    # GUI entry point
├── cli/
│   └── main_cli.py           # CLI entry point
├── app/
│   ├── core/
│   │   └── downloader.py     # Core download logic
│   ├── utils/
│   │   ├── helpers.py        # Utility functions
│   │   └── styles.py         # UI styling
│   └── views/
│       └── main_window.py    # GUI components
├── binaries/                  # FFmpeg location
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── .gitignore                # Git ignore rules
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

### Testing

Run the application in development mode:
```bash
python main.py          # GUI
python cli/main_cli.py  # CLI
```

---

## Troubleshooting

### FFmpeg Not Found
- Ensure `ffmpeg.exe` is in the `binaries/` folder
- Or provide the full path: `--ffmpeg "C:\path\to\ffmpeg.exe"`

### Download Fails
- Check internet connection
- Verify the URL is valid and publicly accessible
- Ensure sufficient disk space
- Update yt_dlp: `pip install --upgrade yt_dlp`

### Permission Denied (CLI)
On Windows, ensure the script execution policy allows it:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

---

## Legal Notice ⚠️

This software is provided for **personal, non-commercial use only**. Users are responsible for:
- Respecting the Terms of Service of each platform
- Complying with copyright and intellectual property laws
- Not circumventing access controls or DRM protection
- Obtaining proper permissions before downloading copyrighted content

The developer is not responsible for misuse of this tool.

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## Support

For issues, feature requests, or questions:
- Open an [Issue](https://github.com/your-username/NONET/issues)
- Submit a [Pull Request](https://github.com/your-username/NONET/pulls)
- Contact: your-email@example.com

---

**Made with ❤️ for media enthusiasts**
