# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

NOTNET: a Windows-only PySide6 + yt-dlp media downloader (MP4 video / MP3 audio at 192 kbps) with three entry points: the GUI, a CLI, and a local HTTP API. There is no linter config, no CI, and no pytest suite.

## Commands

Use the checked-in venv at `venv/` (Python 3.13). Do not recreate it and do not use system Python.

```powershell
venv\Scripts\python.exe main.py                                         # GUI
venv\Scripts\python.exe cli\main_cli.py <URL> [-f mp3|mp4] [-o DIR] [--ffmpeg PATH]
venv\Scripts\python.exe web_server.py [PORT]                            # HTTP API, default 8000, binds 127.0.0.1
venv\Scripts\pyinstaller.exe notnet.spec --noconfirm                    # -> dist\notnet\ + dist\notnet-<version>-win64.zip
```

### Tests (HTTP API only)

`testsprite_tests/` holds TestSprite-generated scripts (untracked). They are standalone scripts, not pytest tests: each one calls its test function at module level, uses `requests`, and expects the API on **port 8123**:

```powershell
venv\Scripts\python.exe web_server.py 8123
venv\Scripts\python.exe testsprite_tests\TC001_get_health_endpoint_returns_server_status.py   # run one test
```

TC003, TC004 and TC006 perform real network downloads into `./descargas`.

## Architecture

The three surfaces don't share one engine. They're built from two separate yt-dlp option builders:

- **GUI**: `main.py` → `app/views/main_window.py` (`VideoDownloader`) → `app/core/downloader.py` (`DownloadWorker.build_options`).
- **CLI**: `cli/main_cli.py` has its own `Downloader._build_options`.
- **HTTP API**: `web_server.py` imports the CLI `Downloader` but only calls `_build_options()`, then runs `YoutubeDL` itself. `Downloader.run()` prints and calls `sys.exit(1)` on error, so it must not be called from the server. Downloads run synchronously inside the request handler (`ThreadingHTTPServer`).

A change to download behaviour (formats, postprocessors, `outtmpl`, `noplaylist`) normally has to be made in both `app/core/downloader.py` and `cli/main_cli.py`. Changing the CLI builder also changes the API. Both builders force real `.mp4` output for video (`format_sort: ['res', 'ext:mp4:m4a']` + `merge_output_format: 'mp4'`); without that, YouTube's VP9/Opus streams merge into `.webm`/`.mkv`. Both also set `concurrent_fragment_downloads: 4`, which speeds up HLS/DASH sources.

Behaviour differs between surfaces:

- **Resolution control is GUI-only.** The GUI maps `NNNp` to `bestvideo[height<=N]+bestaudio/best[height<=N]/best`; the trailing `/best` keeps sites without height metadata working. "Best available" maps to `bestvideo+bestaudio/best`. The CLI and API always use `bestvideo+bestaudio/best` for MP4.
- **Platform detection is display-only.** `helpers.detect_platform()` labels the link under the URL field; it never changes the yt-dlp options. `normalize_url()` adds `https://` to bare links before validation and download.
- **ffmpeg resolution**:
  - GUI: `app/utils/helpers.py` `get_ffmpeg_path()` (`binaries/ffmpeg.exe` from the repo root, or `sys._MEIPASS/binaries` when frozen). It is checked before every download (MP4 merging and MP3 extraction both need it).
  - CLI: `--ffmpeg`, which defaults to `ffmpeg` on PATH.
  - API: `binaries/ffmpeg.exe`, falling back to `ffmpeg` on PATH.

### GUI threading

`DownloadWorker` (`app/core/downloader.py`) is a QObject that `start_download()` moves to a `QThread` **before** connecting its signals. It emits only the terminal signals, from that thread: `succeeded(final_path)`, `failed(message)` or `cancelled()`. Each of them quits the thread, and `QThread.finished` `deleteLater`s both the worker and the thread. The window keeps the worker in `self._worker` because it can't have a parent across threads.

- **Progress is polled, not signalled.** With `concurrent_fragment_downloads > 1`, yt-dlp calls the progress hooks from its own `ThreadPoolExecutor` threads, so the hooks must **never emit Qt signals**. Instead they write into a lock-protected state (`stage`, `title`, `percent`, `speed`, `eta`, plus queued log lines). A 100 ms `QTimer` in the window reads it with `worker.snapshot()` in `poll_progress()`, which also caps UI updates at about 10 per second. A `percent` of `-1.0` means indeterminate and shows a busy bar. `stop_polling()` runs a final poll before stopping the timer.
- **`yt_dlp` is imported inside `run()`**, not at module level. Importing it takes about 0.5 s, and doing it at module level delayed the window on every launch.
- **Cancellation** is cooperative. The GUI owns a `threading.Event`; the progress and postprocessor hooks raise `DownloadCancelled` when it is set, including on fragment threads. An FFmpeg step that is already running can't be interrupted. Afterwards the worker deletes only the files it saw in `downloading` status (`.part`, `-Frag*`, `.ytdl`, unmerged streams). That cleanup runs **after** the `except` block, followed by `gc.collect()` and a few retries: while the traceback is alive it keeps yt-dlp's file handles open, and Windows can't delete open files.
- **Closing mid-download** asks for confirmation, cancels, and ignores the close event. `on_thread_finished` closes the window once the thread stops, so a running `QThread` is never destroyed.
- yt-dlp output is routed through a `logger` object into the Details log (`noprogress`, `color: no_color`). The final file path comes from `post_hooks`.
- Folder, format and quality persist through `QSettings` (organization and application name `NOTNET`, set in `main.configure_app()`).

### Styling

All styling is in `app/utils/styles.py`. `TOKENS` holds colour roles: text tokens are checked for WCAG AA on canvas, surface and input, and `field_border` meets 3:1 against canvas. `TYPE` is a four-step type scale (12/14/20/28 px). `build_styles()` produces the global QSS. Widgets are targeted by `objectName` or by dynamic properties (`class`, `variant`, `state`), and `set_state()` re-polishes them after a change. Avoid inline `setStyleSheet()`, because it cuts the widget off from the global rules. Buttons use `Qt.TabFocus`, so the `:focus` ring appears for keyboard users only. `main.configure_app()` forces `Qt.ColorScheme.Dark`, so the title bar and unstyled popups match the theme. The app icon is drawn by `styles.render_app_icon()` (a `QImage`, which needs no `QGuiApplication`). At runtime `build_app_icon()` wraps it in a `QIcon`; at build time `tools/build_assets.py` writes it to an `.ico`. There is no icon file in the repo.

`main()` sets an explicit AppUserModelID **only for source runs**, so `python.exe` gets its own taskbar icon. The frozen exe must not set one: with an explicit ID and no matching Start-menu shortcut, the Windows 11 taskbar shows a generic icon instead of the exe's embedded one.

### Packaging (`notnet.spec`)

The spec is versioned: `.gitignore` ignores `*.spec` but re-includes `!notnet.spec`. It builds a **one-folder** app, `dist/notnet/` (`notnet.exe` plus `_internal/`), and zips it into `dist/notnet-<version>-win64.zip`, which is the GitHub Releases asset. Don't go back to one-file: that build re-extracted about 370 MB (225 MB of it ffmpeg) to `%TEMP%` on every launch and took 8–10 s to show the window. The folder build takes about 0.8 s. The spec:

- bundles every file in `binaries/` to the `binaries` destination (`_internal/binaries`). That destination name must stay, because `get_ffmpeg_path()` reads it from `sys._MEIPASS`;
- aborts the build if `binaries/ffmpeg.exe` is missing;
- bundles the `curl_cffi` `_wrapper.pyd` and `curl_cffi.libs/*.dll` explicitly, plus hidden imports `curl_cffi.requests` and `yt_dlp.networking._curlcffi`. Without them, TikTok extraction fails in the frozen exe;
- filters unused Qt out of `a.binaries` and `a.datas` with `_QT_EXCLUDES` (`opengl32sw.dll`, Network, OpenGL, Pdf, Qml/Quick, Svg, VirtualKeyboard, most plugins, translations) and excludes `PySide6.QtNetwork`. `qwindows.dll`, Qt6Widgets and Qt6Gui only import Qt6Core and Qt6Gui. If you start using a new Qt module or plugin, remove it from that list;
- builds a windowed exe (`console=False`);
- imports `tools/build_assets.py` (tracked) to write `build/notnet/notnet.ico` from `styles.render_app_icon()` and to build the version resource from `app.__version__`. The `.ico` uses DIB entries below 256 px, because PNG entries render as noise in GDI+;
- after `COLLECT`, calls `write_notices()`, which puts `THIRD_PARTY_NOTICES.md` and `licenses/` next to `notnet.exe`:
  - the FFmpeg version, licence and source link come from `ffmpeg -version`, and the build stops if ffmpeg is `--enable-nonfree`;
  - the Qt/PySide6 section points to the LGPL/GPL texts tracked in `licenses/`;
  - every bundled Python distribution gets its licence files copied;
  - the current `binaries/ffmpeg.exe` is the gyan.dev full_build, which is **GPL-3.0**;
- passes `[('X utf8', None, 'OPTION')]`, because frozen apps ignore `PYTHONUTF8`. `pyi-archive_viewer -l dist/notnet/notnet.exe` should list `X utf8`;
- sets `upx=False` to cut antivirus false positives. UPX isn't installed here anyway.

Run PyInstaller from the repo root, which must not contain an `__init__.py`. Code signing is manual (see README, "Code signing"). Sign `dist\notnet\notnet.exe`, then re-zip.

## Gotchas

- **Language split**: CLI output and argparse help are in **Spanish**. GUI strings and API JSON are in **English**. Match the surface you're editing.
- **`requirements.txt` is UTF-16 LE with a BOM.** Preserve that encoding when editing it, or rewrite it deliberately. Current pin: `yt-dlp[default,curl-cffi]==2026.8.19`. The `curl-cffi` extra is required for TikTok (and is why the spec needs the DLL bundling above). When downloads break (e.g. YouTube 403s), bumping yt-dlp is the usual first fix.
- Gitignored and local-only: `binaries/` (ffmpeg is required at runtime), `venv/`, `build/`, `dist/`, `descargas/` (CLI/API default output dir), and every `*.spec` except `notnet.spec`.
- All downloaders use `noplaylist: True` and `outtmpl` `%(title)s.%(ext)s` in the output dir.
- `AGENTS.md` duplicates some of this guidance for other agents. Keep the two in sync when facts change.
