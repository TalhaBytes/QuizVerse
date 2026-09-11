import math

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPainter, QPen, QLinearGradient, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout,
                               QHBoxLayout, QScrollArea, QTableWidget, QAbstractItemView,
                               QHeaderView, QMessageBox)


def label(text, style="", wrap=True):
    widget = QLabel(str(text))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if style:
        widget.setObjectName(style)
    return widget


def button(text, action, primary=False):
    widget = QPushButton(text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.setObjectName("primary" if primary else "button")
    widget.clicked.connect(action)
    return widget


def row(*widgets):
    layout = QHBoxLayout()
    layout.setSpacing(12)
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def card():
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(12)
    return frame, layout


def metric(title, value):
    frame, layout = card()
    layout.addWidget(label(value, "metric"))
    layout.addWidget(label(title, "muted"))
    return frame


def clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
        elif item.layout():
            clear(item.layout())


def confirm(parent, title, message):
    return QMessageBox.question(parent, title, message,
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes


def avatar_icon(name):
    colors = {"Orbit": "#7760dd", "Nova": "#247e90", "Comet": "#ad553c",
              "Lunar": "#596d9d", "Solar": "#a47c22", "Cosmos": "#9b4d8b"}
    pixmap = QPixmap(56, 56)
    pixmap.fill(Qt.GlobalColor.transparent)
    p = QPainter(pixmap)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(colors.get(name, "#7760dd")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(1, 1, 54, 54)
    p.setPen(QColor("white"))
    p.setFont(QFont("Segoe UI", 21, QFont.Weight.Bold))
    p.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, name[:1])
    p.end()
    return QIcon(pixmap)


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    widget.setAlternatingRowColors(True)
    widget.verticalHeader().hide()
    widget.verticalHeader().setDefaultSectionSize(48)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    widget.horizontalHeader().setStretchLastSection(True)
    widget.setMinimumHeight(250)
    return widget


class Page(QScrollArea):
    def __init__(self, title, subtitle):
        super().__init__()
        self.setWidgetResizable(True)
        container = QWidget()
        container.setObjectName("page")
        self.setWidget(container)
        self.body = QVBoxLayout(container)
        self.body.setContentsMargins(32, 28, 32, 28)
        self.body.setSpacing(20)
        self.body.addWidget(label(title, "title"))
        self.body.addWidget(label(subtitle, "muted"))


class OrbitArt(QWidget):
    """Resolution-independent original artwork; no external image dependency."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(210, 220)

    def sizeHint(self):
        return QSize(280, 260)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.width() / 2, self.height() / 2)
        scale = min(self.width(), self.height()) / 280
        p.scale(scale, scale)
        p.rotate(-23)
        p.setPen(QPen(QColor("#6557a8"), 1.5))
        p.drawEllipse(-118, -64, 236, 128)
        p.drawEllipse(-105, -102, 210, 204)
        gradient = QLinearGradient(-65, -65, 65, 65)
        gradient.setColorAt(0, QColor("#b2a6ff"))
        gradient.setColorAt(1, QColor("#5644ba"))
        p.setBrush(gradient)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(-66, -66, 132, 132)
        p.setBrush(QColor("#69e5cc"))
        p.drawEllipse(97, -14, 19, 19)
        p.setBrush(QColor("#f2c889"))
        p.drawEllipse(-90, -65, 11, 11)
        p.rotate(23)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 60, QFont.Weight.Bold))
        p.drawText(-50, -56, 100, 110, Qt.AlignmentFlag.AlignCenter, "?")
        for i in range(14):
            angle = i * 2.4
            p.setBrush(QColor("#b6b0df"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(int(math.cos(angle) * 125), int(math.sin(angle) * 119), 3, 3)
