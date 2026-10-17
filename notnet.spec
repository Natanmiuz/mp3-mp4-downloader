# -*- mode: python ; coding: utf-8 -*-
# One-folder build: dist/notnet/ (notnet.exe + _internal/) plus a release zip.
# A one-file exe would re-extract ~370 MB (mostly ffmpeg) to %TEMP% on every
# launch, which took 8-10 s; the folder build starts in about 1.5 s.

import glob
import os
import shutil
import sys

import curl_cffi

sys.path.insert(0, SPECPATH)
from app import __version__
from tools.build_assets import version_info, write_ico, write_notices

# The .ico and the version resource are generated from the source on every
# build, so the exe matches build_app_icon() and app.__version__.
_ICON = write_ico(os.path.join(workpath, 'notnet.ico'))

# Bundle every external tool dropped in binaries/ (ffmpeg.exe, ffprobe.exe, ...)
# so the frozen app is self-contained. get_ffmpeg_path() resolves ffmpeg from
# sys._MEIPASS/binaries (_internal/binaries here), so the destination dir must
# stay 'binaries'.
_BIN_DIR = os.path.join(SPECPATH, 'binaries')
_BINARIES = [
    (path, 'binaries')
    for path in sorted(glob.glob(os.path.join(_BIN_DIR, '*')))
    if os.path.isfile(path)
]
if not os.path.isfile(os.path.join(_BIN_DIR, 'ffmpeg.exe')):
    raise SystemExit(
        f'ffmpeg.exe not found in {_BIN_DIR}. MP4 merging and MP3 extraction '
        'would fail in the frozen app; place it there before building.'
    )

# curl_cffi ships an auditwheel-style sibling dir that PyInstaller's hooks miss,
# so bundle its DLLs explicitly or TikTok extraction fails in the frozen exe.
_CURL_CFFI_DIR = os.path.dirname(curl_cffi.__file__)
_CURL_CFFI_BINARIES = [
    (os.path.join(_CURL_CFFI_DIR, '_wrapper.pyd'), 'curl_cffi'),
] + [
    (dll, 'curl_cffi.libs')
    for dll in glob.glob(
        os.path.join(os.path.dirname(_CURL_CFFI_DIR), 'curl_cffi.libs', '*.dll')
    )
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=_BINARIES + _CURL_CFFI_BINARIES,
    datas=[],
    hiddenimports=['curl_cffi.requests', 'yt_dlp.networking._curlcffi'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # PySide6/__init__ imports QtNetwork only optionally (try/except).
    excludes=['PySide6.QtNetwork'],
    noarchive=False,
    optimize=0,
)

# Qt pieces the PySide6 hooks collect that this QtWidgets-only app never loads.
# qwindows.dll, Qt6Widgets and Qt6Gui only depend on Qt6Core/Qt6Gui.
_QT_EXCLUDES = (
    'opengl32sw.dll', 'Qt6Network', 'Qt6OpenGL', 'Qt6Pdf', 'Qt6Qml', 'Qt6Quick',
    'Qt6Svg', 'Qt6VirtualKeyboard', 'qdirect2d',
    'plugins\\generic', 'plugins\\iconengines', 'plugins\\imageformats',
    'plugins\\networkinformation', 'plugins\\platforminputcontexts',
    'plugins\\styles', 'plugins\\tls', 'translations',
)


def _keep(entry):
    name = entry[0].replace('/', '\\')
    return not (name.startswith('PySide6\\') and any(token in name for token in _QT_EXCLUDES))


a.binaries = [entry for entry in a.binaries if _keep(entry)]
a.datas = [entry for entry in a.datas if _keep(entry)]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    # Python UTF-8 mode. Frozen apps ignore PYTHONUTF8 (PyInstaller 6+), and
    # media titles and paths are often non-ASCII.
    [('X utf8', None, 'OPTION')],
    exclude_binaries=True,
    name='notnet',
    icon=_ICON,
    version=version_info(__version__),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # UPX-packed exes trip more antivirus heuristics, and the saving is small.
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='notnet',
)

# FFmpeg (GPL), Qt/PySide6 (LGPL) and the bundled Python packages are
# redistributed, so ship their notices and license texts next to notnet.exe.
_APP_DIR = os.path.join(DISTPATH, 'notnet')
write_notices(_APP_DIR, os.path.join(_BIN_DIR, 'ffmpeg.exe'), [entry[0] for entry in a.pure])

# Release asset for GitHub Releases: notnet-<version>-win64.zip containing notnet/.
shutil.make_archive(os.path.join(DISTPATH, f'notnet-{__version__}-win64'), 'zip', DISTPATH, 'notnet')
