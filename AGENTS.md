# AGENTS.md

PySide6 + yt-dlp desktop downloader. Three entrypoints: GUI (`main.py`), CLI (`cli/main_cli.py`) and HTTP API (`web_server.py`, used for automated tests). No test suite, no linter config, no CI.

## Commands

- Run GUI: `python main.py`
- Run CLI: `python cli/main_cli.py <URL> [-f mp3|mp4] [-o DIR] [--ffmpeg PATH]`
- Run HTTP API: `python web_server.py [PORT]` (default 8000, binds 127.0.0.1)
- Build exe: `pyinstaller notnet.spec` → `dist/notnet.exe`
- Use the checked-in venv at `venv/` (Python 3.13) — do not recreate or use system Python.

## Layout

- `app/core/downloader.py` — shared logic used by the GUI (Qt `Signal`s + `threading.Thread`, not QThread). CLI has its own duplicate `Downloader` class in `cli/main_cli.py`.
- `app/utils/helpers.py:4` — `get_ffmpeg_path()` resolves ffmpeg: frozen-exe uses `sys._MEIPASS/binaries`, source runs use `binaries/` next to repo root.
- `app/views/main_window.py` — the GUI; handles platform/format/resolution validation.
- `web_server.py` — stdlib `http.server` wrapper reusing the CLI `Downloader`; endpoints `GET /health`, `GET /`, `POST /download`.
- `binaries/ffmpeg.exe` is required at runtime but gitignored; MP4 downloads validate it exists.

## Gotchas

- CLI prints in **Spanish**; GUI strings are in **English**. Match whichever surface you're touching.
- yt-dlp version is pinned (`yt-dlp==2026.7.4` in `requirements.txt`); upgrade it when downloads break, as platform changes outpace the pin.
- `.gitignore` ignores `*.spec`, `binaries/`, `venv/`, `build/`, `dist/`, `descargas/`. `notnet.spec` and `dist/notnet.exe` exist only locally and are not tracked.
- Both downloaders set `noplaylist: True` and use `outtmpl` `%(title)s.%(ext)s` in the output dir. MP3 uses FFmpegExtractAudio at 192 kbps.
