"""Build-time assets for notnet.spec: the .ico file, the Windows version resource
and the third-party notices shipped next to notnet.exe.

Run directly to only write the icon: python tools/build_assets.py [OUT.ico]
"""
import os
import platform
import re
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QBuffer, QByteArray, QIODevice
from PySide6.QtGui import QImage
from app import __version__
from app.utils.styles import ICON_SIZES, render_app_icon


def _png_bytes(image):
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def _dib_bytes(image):
    """32-bit BGRA DIB entry: bottom-up rows plus an all-clear AND mask."""
    image = image.convertToFormat(QImage.Format_ARGB32)
    width, height = image.width(), image.height()
    stride = image.bytesPerLine()
    raw = bytes(image.constBits())
    rows = [raw[y * stride:y * stride + width * 4] for y in range(height)]
    pixels = b''.join(reversed(rows))
    mask = b'\x00' * (((width + 31) // 32) * 4) * height
    header = struct.pack('<IiiHHIIiiII', 40, width, height * 2, 1, 32, 0, len(pixels) + len(mask), 0, 0, 0, 0)
    return header + pixels + mask


def write_ico(path):
    """Writes a multi-size .ico: DIB entries below 256 px (readable by every
    Windows API, including GDI+), PNG for the 256 px entry."""
    images = [
        (size, _png_bytes(render_app_icon(size)) if size >= 256 else _dib_bytes(render_app_icon(size)))
        for size in ICON_SIZES
    ]
    header = struct.pack('<HHH', 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, blobs = b'', b''
    for size, data in images:
        dimension = 0 if size >= 256 else size  # 0 means 256 in the ICO format
        entries += struct.pack('<BBBBHHII', dimension, dimension, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
        blobs += data
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(header + entries + blobs)
    return path


def version_info(version=__version__):
    """VSVersionInfo for EXE(version=...); shown in Explorer's Details tab."""
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo, StringFileInfo, StringStruct, StringTable,
        VarFileInfo, VarStruct, VSVersionInfo,
    )
    numbers = (tuple(int(part) for part in version.split('.')) + (0, 0, 0, 0))[:4]
    strings = [
        StringStruct('CompanyName', 'Natanmiuz'),
        StringStruct('FileDescription', 'NOTNET Media Downloader'),
        StringStruct('FileVersion', version),
        StringStruct('InternalName', 'notnet'),
        StringStruct('LegalCopyright', 'Copyright (c) Natanmiuz. Personal, non-commercial use only.'),
        StringStruct('OriginalFilename', 'notnet.exe'),
        StringStruct('ProductName', 'NOTNET'),
        StringStruct('ProductVersion', version),
    ]
    return VSVersionInfo(
        ffi=FixedFileInfo(filevers=numbers, prodvers=numbers),
        kids=[
            StringFileInfo([StringTable('040904B0', strings)]),
            VarFileInfo([VarStruct('Translation', [0x0409, 1200])]),
        ],
    )


def ffmpeg_info(ffmpeg_path):
    """Version, SPDX license and source link of an ffmpeg binary, read from
    `ffmpeg -version`. Refuses non-redistributable (--enable-nonfree) builds."""
    output = subprocess.run([ffmpeg_path, '-hide_banner', '-version'], capture_output=True,
                            encoding='utf-8', errors='replace', check=True).stdout
    version = output.split()[2]
    config = next((line for line in output.splitlines() if line.startswith('configuration:')), '')
    if '--enable-nonfree' in config:
        raise SystemExit(f'{ffmpeg_path} was built with --enable-nonfree and cannot be redistributed.')
    if '--enable-gpl' in config:
        spdx = 'GPL-3.0-or-later' if '--enable-version3' in config else 'GPL-2.0-or-later'
    else:
        spdx = 'LGPL-3.0-or-later' if '--enable-version3' in config else 'LGPL-2.1-or-later'
    commit = re.search(r'git-([0-9a-f]{7,40})', version)
    source = (f'https://github.com/FFmpeg/FFmpeg/commit/{commit.group(1)}' if commit
              else f'https://ffmpeg.org/releases/ffmpeg-{version.lstrip("n")}.tar.xz')
    return version, spdx, source


def _license_name(meta):
    classifier = next((c.split('::')[-1].strip() for c in meta.get_all('Classifier') or []
                       if c.startswith('License ::')), '')
    return meta.get('License-Expression') or classifier or (meta.get('License') or 'see files').splitlines()[0][:60]


def collect_python_licenses(module_names, dest_dir):
    """Copies the license files of every distribution that provides one of the
    bundled modules. Returns (name, version, license, [copied paths])."""
    from importlib import metadata
    by_top = metadata.packages_distributions()
    names = {dist for module in module_names for dist in by_top.get(module.split('.')[0], [])}
    names.discard('PySide6_Addons')  # its modules are excluded from the build
    packages = []
    for name in sorted(names, key=str.lower):
        dist = metadata.distribution(name)
        copied = []
        for entry in dist.files or []:
            # PySide6 wheels only carry the Qt commercial license; the LGPL texts
            # used for this build are in licenses/ instead.
            if entry.name == 'LicenseRef-Qt-Commercial.txt' or not re.search(r'LICEN[CS]E|COPYING|NOTICE', entry.name, re.I):
                continue
            target = os.path.join(dest_dir, 'licenses', 'python', name, entry.name)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(entry.locate(), target)
            copied.append(os.path.relpath(target, dest_dir).replace('\\', '/'))
        packages.append((dist.metadata['Name'], dist.version, _license_name(dist.metadata), copied))
    return packages


def write_notices(dest_dir, ffmpeg_path, module_names):
    """Writes THIRD_PARTY_NOTICES.md and licenses/ into the built app folder."""
    shutil.copytree(os.path.join(ROOT, 'licenses'), os.path.join(dest_dir, 'licenses'), dirs_exist_ok=True)
    python_license = os.path.join(sys.base_prefix, 'LICENSE.txt')
    if os.path.isfile(python_license):
        os.makedirs(os.path.join(dest_dir, 'licenses', 'python', 'Python'), exist_ok=True)
        shutil.copyfile(python_license, os.path.join(dest_dir, 'licenses', 'python', 'Python', 'LICENSE.txt'))
    packages = collect_python_licenses(module_names, dest_dir)
    ff_version, ff_spdx, ff_source = ffmpeg_info(ffmpeg_path)
    ff_text = 'licenses/GPL-3.0.txt' if ff_spdx.startswith('GPL-3') else 'licenses/LGPL-3.0.txt and licenses/GPL-3.0.txt'
    if ff_spdx.endswith('2.0-or-later') or ff_spdx.startswith('LGPL-2'):
        ff_text = 'https://www.gnu.org/licenses/'
    qt_version = next((version for name, version, *_ in packages if name.lower().startswith('pyside6')), '')

    lines = [
        '# Third-party notices',
        '',
        f'NOTNET {__version__} bundles the software below. Each component keeps its own license;',
        'the license texts are in the `licenses` folder next to this file.',
        '',
        '## FFmpeg',
        '',
        f'- Version: `{ff_version}`',
        f'- License: {ff_spdx} (from its build configuration)',
        f'- Corresponding source: {ff_source}',
    ]
    if 'gyan.dev' in ff_version:
        lines.append('- Build provider and included libraries: https://www.gyan.dev/ffmpeg/builds/')
    lines += [
        f'- License text: {ff_text}',
        '',
        'NOTNET runs `_internal/binaries/ffmpeg.exe` as a separate program; it is not linked into NOTNET.',
        '',
        '## Qt and Qt for Python (PySide6)',
        '',
        f'- Version: {qt_version}, used under LGPL-3.0-only (`licenses/LGPL-3.0.txt`, which adds to `licenses/GPL-3.0.txt`)',
        '- Source: https://download.qt.io/official_releases/QtForPython/ and https://download.qt.io/official_releases/qt/',
        '- The Qt and PySide6 libraries are separate DLLs in `_internal/PySide6` and can be replaced with compatible builds.',
        '',
        '## Python',
        '',
        f'- Version {platform.python_version()}, PSF License: `licenses/python/Python/LICENSE.txt`',
        '',
        '## Python packages',
        '',
        '| Package | Version | License | License files |',
        '|---|---|---|---|',
    ]
    for name, version, license_name, copied in packages:
        files = ', '.join(f'`{path}`' for path in copied) or 'see `licenses/`'
        lines.append(f'| {name} | {version} | {license_name} | {files} |')
    with open(os.path.join(dest_dir, 'THIRD_PARTY_NOTICES.md'), 'w', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    print(write_ico(sys.argv[1] if len(sys.argv) > 1 else os.path.join('build', 'notnet.ico')))
