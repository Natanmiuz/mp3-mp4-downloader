# AGENTS.md

PySide6 + yt-dlp desktop downloader with three entrypoints: GUI (`main.py`), CLI (`cli/main_cli.py`) and HTTP API (`web_server.py`, used for automated tests). There is no pytest suite, no linter config and no CI.

## Commands

- Run GUI: `python main.py`
- Run CLI: `python cli/main_cli.py <URL> [-f mp3|mp4] [-o DIR] [--ffmpeg PATH]`
- Run HTTP API: `python web_server.py [PORT]` (default 8000, binds 127.0.0.1)
- Build: `pyinstaller notnet.spec --noconfirm` → `dist/notnet/` (`notnet.exe` + `_internal/`) and `dist/notnet-<version>-win64.zip` (the Releases asset)
- API tests: start `python web_server.py 8123`, then run a script directly, e.g. `python testsprite_tests/TC001_get_health_endpoint_returns_server_status.py`. These are untracked TestSprite scripts, not pytest tests. TC003, TC004 and TC006 do real network downloads.
- Use the checked-in venv at `venv/` (Python 3.13). Do not recreate it and do not use system Python.

## Layout

- `app/core/downloader.py`: the GUI's `DownloadWorker`, a QObject moved to a `QThread` (move first, then connect). It only emits `succeeded`/`failed`/`cancelled`. With 4 concurrent fragments, yt-dlp calls the hooks from its own threads, so the hooks write into a lock-protected state that the window polls every 100 ms (`snapshot()`) and must never emit Qt signals. `yt_dlp` is imported inside `run()` to keep startup fast. Cancelling sets a `threading.Event` that the hooks check, and the partial files are removed after the `except` block, once the traceback has released the file handles. The CLI has its own duplicate `Downloader` class in `cli/main_cli.py`, so download-option changes usually need to be made in both files. Both force `.mp4` output for video (`format_sort` + `merge_output_format`) and download 4 fragments in parallel.
- `app/utils/helpers.py`: `get_ffmpeg_path()` resolves ffmpeg. The frozen exe uses `sys._MEIPASS/binaries`; source runs use `binaries/` in the repo root. The file also has `normalize_url`/`validate_url`, `detect_platform` (a display-only label) and `describe_error` (plain-language yt-dlp errors).
- `app/views/main_window.py`: the GUI. It handles validation, the progress panel, cancel and close-while-downloading, and keeps folder/format/quality in `QSettings`. Resolution control exists only in the GUI; the CLI and API always use `bestvideo+bestaudio/best` for MP4.
- `app/utils/styles.py`: `TOKENS` (WCAG-checked colours), the `TYPE` scale, the global QSS and the app icon (`render_app_icon()` returns a `QImage`, reused by the build for the `.ico`). Style widgets through `objectName` or dynamic properties, never with inline `setStyleSheet`.
- `main.py`: sets an explicit AppUserModelID only for source runs. The frozen exe must not set one, because Windows 11 then shows a generic taskbar icon.
- `web_server.py`: stdlib `http.server` wrapper. It reuses the CLI `Downloader._build_options()` but not `run()`, because `run()` calls `sys.exit`. Endpoints: `GET /health`, `GET /`, `POST /download`.
- `binaries/ffmpeg.exe` is required at runtime but gitignored. The GUI checks that it exists before every download. The CLI defaults to `ffmpeg` on PATH (`--ffmpeg` overrides it). The API uses `binaries/ffmpeg.exe` and falls back to PATH.

## Gotchas

- CLI prints in **Spanish**; GUI strings are in **English**. Match whichever surface you're touching.
- yt-dlp is pinned as `yt-dlp[default,curl-cffi]==2026.8.19` in `requirements.txt`. Upgrade it when downloads break, since platform changes outpace the pin. The `curl-cffi` extra is required for TikTok.
- `requirements.txt` is UTF-16 LE with a BOM. Preserve that encoding when editing it.
- `.gitignore` ignores `*.spec`, `binaries/`, `venv/`, `build/`, `dist/`, `descargas/`, but re-includes `!notnet.spec`, so the spec is versioned and the build output is not. The spec builds **one folder**, not one file: one-file re-extracted about 370 MB on every launch, taking 8–10 s, while the folder build takes about 0.8 s. It bundles `binaries/*` to `binaries` (that destination name must stay for `get_ffmpeg_path()`), aborts if `ffmpeg.exe` is missing or is a `nonfree` build, bundles `curl_cffi` DLLs explicitly, and drops unused Qt modules and plugins (`_QT_EXCLUDES`). Through the tracked `tools/build_assets.py` (version from `app.__version__`) it generates the icon, the version resource, `THIRD_PARTY_NOTICES.md` and `licenses/`. The bundled ffmpeg is GPL-3.0. It also enables UTF-8 mode (`X utf8` option), disables UPX and zips the folder.
- Both downloaders set `noplaylist: True` and use `outtmpl` `%(title)s.%(ext)s` in the output dir. MP3 uses FFmpegExtractAudio at 192 kbps.
- `CLAUDE.md` holds the fuller version of this guidance. Keep the two in sync.
