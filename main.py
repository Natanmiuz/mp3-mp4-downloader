import sys
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from app.utils.styles import build_app_icon, build_styles
from app.views.main_window import VideoDownloader


def configure_app(app):
    app.setOrganizationName("NOTNET")
    app.setApplicationName("NOTNET")
    app.setStyle("Fusion")
    # The stylesheet is dark-only; this keeps the title bar and any unstyled
    # popup (e.g. QLineEdit's context menu) on the same scheme.
    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    app.setFont(QFont("Segoe UI", 10))
    app.setWindowIcon(build_app_icon())
    app.setStyleSheet(build_styles())


def main():
    if sys.platform == "win32" and not getattr(sys, "frozen", False):
        # Source runs only: gives python.exe its own taskbar identity so the
        # window icon shows. The frozen exe must keep its exe-derived identity;
        # an explicit ID with no matching shortcut makes Windows 11 show a
        # generic taskbar icon instead of the exe's embedded one.
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NOTNET.Downloader")
    app = QApplication(sys.argv)
    configure_app(app)
    window = VideoDownloader()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
