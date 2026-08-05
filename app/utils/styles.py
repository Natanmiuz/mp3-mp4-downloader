import os
import tempfile
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QPen, QColor

TOKENS = {
    "canvas": "#0B0E13",
    "surface": "#12161D",
    "surface_hover": "#1B222D",
    "input": "#0E1218",
    "border": "rgba(255, 255, 255, 0.07)",
    "border_strong": "rgba(255, 255, 255, 0.15)",
    "text": "#E8EDF3",
    "text_secondary": "#9AA7B5",
    "text_muted": "#64748B",
    "accent": "#F5A623",
    "accent_hover": "#F7B84A",
    "accent_pressed": "#D48F14",
    "accent_text": "#211505",
    "success": "#34C27A",
    "error": "#E5484D",
    "disabled_bg": "#23272E",
}

FONT_STACK = '"Segoe UI Variable", "Segoe UI", "Arial"'
MONO_STACK = '"Cascadia Code", "Consolas", "monospace"'


def ensure_combo_arrow():
    path = os.path.join(tempfile.gettempdir(), "notnet_combo_arrow.png")
    if not os.path.isfile(path):
        img = QImage(12, 8, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(TOKENS["text_secondary"]))
        pen.setWidthF(1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(1, 1, 6, 6)
        painter.drawLine(6, 6, 11, 1)
        painter.end()
        img.save(path)
    return path.replace("\\", "/")


def build_styles():
    arrow = ensure_combo_arrow()
    t = TOKENS
    return f"""
    QMainWindow, QMessageBox {{
        background-color: {t['canvas']};
    }}
    QWidget {{
        color: {t['text']};
        font-family: {FONT_STACK};
    }}
    QToolTip {{
        background-color: {t['surface_hover']};
        color: {t['text']};
        border: 1px solid {t['border_strong']};
        padding: 6px 8px;
    }}
    QMessageBox QLabel {{
        color: {t['text']};
    }}

    QLabel[class="section-label"] {{
        color: {t['text_secondary']};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
    }}
    QLabel[class="note"] {{
        color: {t['text_muted']};
        font-size: 12px;
    }}
    QLabel#brandDot {{
        color: {t['accent']};
        font-size: 12px;
    }}
    QLabel#appTitle {{
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 2px;
    }}
    QLabel#appSubtitle {{
        color: {t['text_muted']};
        font-size: 12px;
    }}

    QLineEdit, QComboBox, QTextEdit {{
        background-color: {t['input']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 9px 12px;
        color: {t['text']};
        selection-background-color: {t['accent']};
        selection-color: {t['accent_text']};
        outline: none;
    }}
    QLineEdit:hover, QComboBox:hover, QTextEdit:hover {{
        border-color: {t['border_strong']};
    }}
    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
        border-color: {t['accent']};
    }}
    QLineEdit:disabled, QComboBox:disabled {{
        color: {t['text_muted']};
        border-color: {t['border']};
    }}

    QLineEdit#urlField {{
        font-size: 15px;
        padding: 14px 16px;
        border-radius: 10px;
        border: 1px solid {t['border_strong']};
    }}
    QLineEdit#urlField:focus {{
        border-color: {t['accent']};
    }}

    QComboBox {{
        padding-right: 30px;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox::down-arrow {{
        image: url("{arrow}");
        width: 12px;
        height: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border_strong']};
        selection-background-color: {t['surface_hover']};
        selection-color: {t['text']};
        outline: none;
    }}

    QPushButton {{
        background-color: {t['surface']};
        color: {t['text_secondary']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 9px 16px;
        font-weight: 500;
        font-size: 13px;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {t['surface_hover']};
        color: {t['text']};
        border-color: {t['border_strong']};
    }}
    QPushButton:pressed {{
        background-color: #161C24;
    }}
    QPushButton:disabled {{
        color: {t['text_muted']};
        background-color: {t['surface']};
        border-color: {t['border']};
    }}

    QPushButton[variant="primary"] {{
        background-color: {t['accent']};
        color: {t['accent_text']};
        border: none;
        font-weight: 700;
        font-size: 14px;
        padding: 12px 24px;
        border-radius: 10px;
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {t['accent_hover']};
    }}
    QPushButton[variant="primary"]:pressed {{
        background-color: {t['accent_pressed']};
    }}
    QPushButton[variant="primary"]:disabled {{
        background-color: rgba(255, 176, 46, 0.22);
        color: rgba(255, 255, 255, 0.30);
    }}

    QFrame#segmented {{
        background-color: {t['input']};
        border: 1px solid {t['border']};
        border-radius: 10px;
    }}
    QFrame#segmented QPushButton {{
        background: transparent;
        border: none;
        border-radius: 8px;
        color: {t['text_secondary']};
        font-weight: 600;
        font-size: 13px;
        padding: 9px;
        margin: 3px;
    }}
    QFrame#segmented QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.05);
        color: {t['text']};
    }}
    QFrame#segmented QPushButton:checked {{
        background-color: {t['accent']};
        color: {t['accent_text']};
    }}

    QFrame#progressPanel {{
        background-color: {t['surface']};
        border: 1px solid {t['border']};
        border-radius: 12px;
    }}
    QLabel#stageLabel {{
        color: {t['text_secondary']};
        font-size: 12px;
        font-weight: 500;
    }}
    QLabel#stageLabel[state="success"] {{
        color: {t['success']};
        font-weight: 600;
    }}
    QLabel#stageLabel[state="error"] {{
        color: {t['error']};
        font-weight: 600;
    }}
    QLabel#percentLabel {{
        font-size: 26px;
        font-weight: 700;
    }}
    QLabel#percentLabel[state="success"] {{
        color: {t['success']};
    }}
    QLabel#percentLabel[state="error"] {{
        color: {t['error']};
    }}
    QLabel#speedLabel {{
        color: {t['text_muted']};
        font-size: 11px;
    }}

    QProgressBar {{
        background-color: {t['input']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        min-height: 14px;
        max-height: 14px;
    }}
    QProgressBar::chunk {{
        background-color: {t['accent']};
        border-radius: 5px;
    }}
    QProgressBar[state="success"]::chunk {{
        background-color: {t['success']};
    }}
    QProgressBar[state="error"]::chunk {{
        background-color: {t['error']};
    }}

    QPushButton#detailsToggle {{
        background: transparent;
        border: none;
        color: {t['text_muted']};
        padding: 4px;
        font-size: 11px;
        font-weight: 500;
    }}
    QPushButton#detailsToggle:hover {{
        color: {t['text_secondary']};
    }}

    QTextEdit#logOutput {{
        font-family: {MONO_STACK};
        font-size: 11px;
        color: {t['text_secondary']};
        background-color: {t['canvas']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 8px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.12);
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.22);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    """
