import os
import tempfile
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QImage, QPainter, QPen, QColor, QIcon, QPixmap, QPainterPath

# Colour roles. Text tokens are checked for WCAG AA (>= 4.5:1) on canvas,
# surface and input; field_border meets the 3:1 non-text minimum on canvas.
TOKENS = {
    "canvas": "#0B0E13",
    "surface": "#12161D",
    "surface_hover": "#1B222D",
    "surface_pressed": "#161C24",
    "input": "#0E1218",
    "border": "rgba(255, 255, 255, 0.07)",
    "border_strong": "rgba(255, 255, 255, 0.15)",
    "field_border": "#586273",
    "field_border_hover": "#717D8F",
    "text": "#E8EDF3",
    "text_secondary": "#9AA7B5",
    "text_muted": "#7A8796",
    "accent": "#F5A623",
    "accent_hover": "#F7B84A",
    "accent_pressed": "#D48F14",
    "accent_text": "#211505",
    "accent_disabled": "rgba(245, 166, 35, 0.22)",
    "success": "#34C27A",
    "error": "#F2555A",
}

# Modular type scale (base 14 px, minor third ~1.2): ms(-1), ms(0), ms(2), ms(4).
TYPE = {
    "caption": 12,
    "body": 14,
    "title": 20,
    "display": 28,
}

FONT_STACK = '"Segoe UI Variable", "Segoe UI", "Arial"'
MONO_STACK = '"Cascadia Code", "Consolas", "monospace"'


def ensure_combo_arrow():
    color = TOKENS["text_secondary"].lstrip("#")
    path = os.path.join(tempfile.gettempdir(), f"notnet_combo_arrow_{color}.png")
    if not os.path.isfile(path):
        # Drawn at 3x and shown at 12x8 so it stays crisp up to 300% scaling.
        img = QImage(36, 24, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(TOKENS["text_secondary"]))
        pen.setWidthF(4.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(QPointF(4, 4), QPointF(18, 18))
        painter.drawLine(QPointF(18, 18), QPointF(32, 4))
        painter.end()
        img.save(path)
    return path.replace("\\", "/")


ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def render_app_icon(size):
    """Amber rounded tile with a download arrow. Returns a QImage, so the
    build script can render it without a QGuiApplication."""
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(TOKENS["accent"]))
    radius = size * 0.22
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    pen = QPen(QColor(TOKENS["accent_text"]))
    pen.setWidthF(max(1.5, size * 0.1))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    s = size / 32
    painter.drawLine(QPointF(16 * s, 7 * s), QPointF(16 * s, 19 * s))
    arrow = QPainterPath(QPointF(10.5 * s, 14 * s))
    arrow.lineTo(16 * s, 19.5 * s)
    arrow.lineTo(21.5 * s, 14 * s)
    painter.drawPath(arrow)
    painter.drawLine(QPointF(9 * s, 24.5 * s), QPointF(23 * s, 24.5 * s))
    painter.end()
    return image


def build_app_icon():
    icon = QIcon()
    for size in ICON_SIZES:
        icon.addPixmap(QPixmap.fromImage(render_app_icon(size)))
    return icon


def build_styles():
    arrow = ensure_combo_arrow()
    t = TOKENS
    f = TYPE
    return f"""
    QMainWindow, QMessageBox {{
        background-color: {t['canvas']};
    }}
    QWidget {{
        color: {t['text']};
        font-family: {FONT_STACK};
        font-size: {f['body']}px;
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
    QMenu {{
        background-color: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border_strong']};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {t['surface_hover']};
    }}
    QMenu::item:disabled {{
        color: {t['text_muted']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {t['border_strong']};
        margin: 4px 8px;
    }}

    QLabel[class="section-label"] {{
        color: {t['text_secondary']};
        font-size: {f['caption']}px;
        font-weight: 600;
        letter-spacing: 1px;
    }}
    QLabel#appTitle {{
        font-size: {f['title']}px;
        font-weight: 700;
        letter-spacing: 2px;
    }}
    QLabel#appSubtitle {{
        color: {t['text_muted']};
        font-size: {f['caption']}px;
    }}
    QLabel#urlHint {{
        color: {t['text_muted']};
        font-size: {f['caption']}px;
    }}
    QLabel#urlHint[state="detected"] {{
        color: {t['success']};
    }}
    QLabel#urlHint[state="error"] {{
        color: {t['error']};
    }}

    QLineEdit, QComboBox, QTextEdit {{
        background-color: {t['input']};
        border: 1px solid {t['field_border']};
        border-radius: 8px;
        padding: 9px 12px;
        color: {t['text']};
        selection-background-color: {t['accent']};
        selection-color: {t['accent_text']};
        outline: none;
    }}
    QLineEdit:hover, QComboBox:hover {{
        border-color: {t['field_border_hover']};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border-color: {t['accent']};
    }}
    QLineEdit:disabled, QComboBox:disabled {{
        color: {t['text_muted']};
        border-color: {t['border_strong']};
    }}
    QLineEdit[readOnly="true"] {{
        color: {t['text_secondary']};
    }}

    QLineEdit#urlField {{
        padding: 13px 16px;
        border-radius: 10px;
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
        padding: 4px;
    }}

    QLabel#audioNote {{
        color: {t['text_secondary']};
        background-color: {t['input']};
        border: 1px dashed {t['border_strong']};
        border-radius: 8px;
        padding: 9px 12px;
    }}

    QPushButton {{
        background-color: {t['surface']};
        color: {t['text_secondary']};
        border: 1px solid {t['border_strong']};
        border-radius: 8px;
        padding: 9px 16px;
        font-weight: 500;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {t['surface_hover']};
        color: {t['text']};
        border-color: {t['field_border']};
    }}
    QPushButton:focus {{
        color: {t['text']};
        border-color: {t['accent']};
    }}
    QPushButton:pressed {{
        background-color: {t['surface_pressed']};
    }}
    QPushButton:disabled {{
        color: {t['text_muted']};
        background-color: {t['surface']};
        border-color: {t['border']};
    }}

    QPushButton[variant="primary"] {{
        background-color: {t['accent']};
        color: {t['accent_text']};
        border: 2px solid transparent;
        font-weight: 600;
        padding: 11px 24px;
        border-radius: 10px;
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {t['accent_hover']};
    }}
    QPushButton[variant="primary"]:focus {{
        border-color: {t['text']};
    }}
    QPushButton[variant="primary"]:pressed {{
        background-color: {t['accent_pressed']};
    }}
    QPushButton[variant="primary"]:disabled {{
        background-color: {t['accent_disabled']};
        color: {t['text_muted']};
    }}

    QPushButton[variant="link"] {{
        background: transparent;
        border: none;
        color: {t['text_secondary']};
        padding: 6px 4px;
    }}
    QPushButton[variant="link"]:hover {{
        color: {t['text']};
    }}
    QPushButton[variant="link"]:focus {{
        color: {t['text']};
        text-decoration: underline;
    }}

    QFrame#segmented {{
        background-color: {t['input']};
        border: 1px solid {t['field_border']};
        border-radius: 10px;
    }}
    QFrame#segmented QPushButton {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 7px;
        color: {t['text_secondary']};
        font-weight: 600;
        padding: 7px 10px;
    }}
    QFrame#segmented QPushButton:hover {{
        background-color: rgba(255, 255, 255, 0.05);
        color: {t['text']};
    }}
    QFrame#segmented QPushButton:focus {{
        border-color: {t['text']};
    }}
    QFrame#segmented QPushButton:checked {{
        background-color: {t['accent']};
        color: {t['accent_text']};
    }}
    QFrame#segmented QPushButton:checked:focus {{
        border-color: {t['canvas']};
    }}
    QFrame#segmented QPushButton:disabled {{
        color: {t['text_muted']};
    }}
    QFrame#segmented QPushButton:checked:disabled {{
        background-color: {t['accent_disabled']};
        color: {t['text_muted']};
    }}

    QFrame#progressPanel {{
        background-color: {t['surface']};
        border: 1px solid {t['border_strong']};
        border-radius: 12px;
    }}
    QLabel#stageLabel {{
        color: {t['text_secondary']};
        font-weight: 600;
    }}
    QLabel#stageLabel[state="success"] {{
        color: {t['success']};
    }}
    QLabel#stageLabel[state="error"] {{
        color: {t['error']};
    }}
    QLabel#percentLabel {{
        font-size: {f['display']}px;
        font-weight: 600;
    }}
    QLabel#percentLabel[state="success"] {{
        color: {t['success']};
    }}
    QLabel#mediaTitle {{
        color: {t['text']};
    }}
    QLabel#infoLabel {{
        color: {t['text_secondary']};
    }}
    QLabel#infoLabel[state="error"] {{
        color: {t['text']};
    }}

    QProgressBar {{
        background-color: {t['input']};
        border: 1px solid {t['border_strong']};
        border-radius: 6px;
        min-height: 12px;
        max-height: 12px;
    }}
    QProgressBar::chunk {{
        background-color: {t['accent']};
        border-radius: 5px;
    }}
    QProgressBar[state="success"]::chunk {{
        background-color: {t['success']};
    }}

    QTextEdit#logOutput {{
        font-family: {MONO_STACK};
        font-size: {f['caption']}px;
        color: {t['text_secondary']};
        background-color: {t['canvas']};
        border: 1px solid {t['border_strong']};
        border-radius: 8px;
        padding: 8px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.18);
        border-radius: 5px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.28);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: transparent;
    }}
    """
