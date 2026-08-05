import sys
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from app.utils.styles import build_styles
from app.views.main_window import VideoDownloader

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(build_styles())
    window = VideoDownloader()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()