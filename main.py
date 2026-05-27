import sys
from PySide6.QtWidgets import QApplication
from app.views.main_window import VideoDownloader

def main():
    app = QApplication(sys.argv)
    window = VideoDownloader()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()