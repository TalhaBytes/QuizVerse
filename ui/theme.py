from PySide6.QtGui import QColor, QPalette
from utils.paths import resource_path


def apply_theme(app, theme):
    dark = theme == "Dark"
    bg, surface, raised = ("#0d1221", "#161e31", "#202c43") if dark else ("#f1f4fa", "#ffffff", "#e7edf7")
    text, muted, border = ("#edf2ff", "#a9b8d3", "#2e3d57") if dark else ("#17233b", "#52627c", "#c9d4e5")
    accent = "#aaa0ff" if dark else "#5845b4"
    up = resource_path("assets/icons/up.svg").as_posix()
    down = resource_path("assets/icons/down.svg").as_posix()
    palette = QPalette()
    for role, color in ((QPalette.ColorRole.Window, bg), (QPalette.ColorRole.WindowText, text),
                        (QPalette.ColorRole.Base, surface), (QPalette.ColorRole.AlternateBase, raised),
                        (QPalette.ColorRole.Text, text), (QPalette.ColorRole.Button, surface),
                        (QPalette.ColorRole.ButtonText, text), (QPalette.ColorRole.Highlight, "#635bdb"),
                        (QPalette.ColorRole.HighlightedText, "#ffffff"),
                        (QPalette.ColorRole.ToolTipBase, surface), (QPalette.ColorRole.ToolTipText, text)):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(f"""
        QWidget {{ color: {text}; font-family: 'Segoe UI'; font-size: 14px; }}
        QMainWindow, QDialog, QScrollArea, QWidget#page {{ background: {bg}; }}
        QScrollArea {{ border: none; }}
        QFrame#sidebar, QFrame#card {{ background: {surface}; border: 1px solid {border}; border-radius: 16px; }}
        QFrame#sidebar {{ border-radius: 0px; border-width: 0px 1px 0px 0px; }}
        QLabel {{ background: transparent; }}
        QLabel#title {{ font-size: 30px; font-weight: 700; }}
        QLabel#heroTitle {{ font-size: 42px; font-weight: 800; }}
        QLabel#section {{ font-size: 19px; font-weight: 650; }}
        QLabel#muted {{ color: {muted}; }}
        QLabel#eyebrow {{ color: {accent}; font-size: 12px; font-weight: 700; }}
        QLabel#metric {{ font-size: 30px; font-weight: 700; }}
        QLabel#brand {{ font-size: 23px; font-weight: 800; }}
        QPushButton {{ background: {raised}; border: 1px solid {border}; border-radius: 10px;
                        padding: 11px 18px; font-weight: 600; min-height: 21px; }}
        QPushButton:hover {{ border-color: #9a90ff; background: {surface}; }}
        QPushButton:pressed {{ background: #5146a7; color: white; }}
        QPushButton:focus {{ border: 2px solid #b4abff; }}
        QPushButton:disabled {{ color: {muted}; background: {surface}; }}
        QPushButton#primary {{ background: #7160ed; color: white; border-color: #9183fa; }}
        QPushButton#primary:hover {{ background: #8271fa; }}
        QPushButton#danger {{ color: #ed718b; }}
        QPushButton#nav {{ text-align: left; background: transparent; border: none; padding: 14px 16px; }}
        QPushButton#nav:checked {{ background: {raised}; color: {accent}; border-left: 3px solid #9485ff; }}
        QPushButton#choice {{ text-align: left; padding: 18px; font-size: 16px; }}
        QPushButton#correct {{ background: #174e43; color: #c5ffe9; border: 2px solid #54d6ae; text-align: left; padding: 18px; font-size: 16px; }}
        QPushButton#incorrect {{ background: #512839; color: #ffd8e1; border: 2px solid #ec819d; text-align: left; padding: 18px; font-size: 16px; }}
        QPushButton#correct QLabel {{ color: #c5ffe9; }}
        QPushButton#incorrect QLabel {{ color: #ffd8e1; }}
        QLineEdit, QTextEdit, QComboBox, QSpinBox {{ background: {surface}; border: 1px solid {border};
                        border-radius: 8px; padding: 9px; selection-background-color: #7160ed; }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: #a99eff; }}
        QComboBox QAbstractItemView {{ background: {surface}; selection-background-color: #5146a7; }}
        QComboBox, QSpinBox {{ padding-right: 32px; }}
        QComboBox::drop-down {{ subcontrol-origin: border; subcontrol-position: top right; width: 28px; border: none; }}
        QComboBox::down-arrow {{ image: url("{down}"); width: 12px; height: 12px; }}
        QSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 28px; border-left: 1px solid {border}; border-bottom: 1px solid {border}; }}
        QSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 28px; border-left: 1px solid {border}; }}
        QSpinBox::up-arrow {{ image: url("{up}"); width: 12px; height: 8px; }}
        QSpinBox::down-arrow {{ image: url("{down}"); width: 12px; height: 8px; }}
        QCheckBox {{ spacing: 12px; padding: 6px 0px; }}
        QCheckBox::indicator {{ width: 20px; height: 20px; }}
        QProgressBar {{ background: {raised}; border: none; border-radius: 5px; height: 10px; text-align: center; }}
        QProgressBar::chunk {{ background: #8b7cf5; border-radius: 5px; }}
        QTableWidget, QListWidget {{ background: {surface}; alternate-background-color: {raised};
                        border: 1px solid {border}; border-radius: 10px; gridline-color: {border}; }}
        QTableWidget::item, QListWidget::item {{ padding: 9px; }}
        QTableWidget::item:selected, QListWidget::item:selected {{ background: #5146a7; color: white; }}
        QHeaderView::section {{ background: {raised}; border: none; padding: 11px; color: {muted}; font-weight: 600; }}
        QScrollBar:vertical {{ background: {bg}; width: 10px; }}
        QScrollBar::handle:vertical {{ background: {border}; border-radius: 5px; min-height: 30px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QToolTip {{ background: {surface}; color: {text}; border: 1px solid {border}; padding: 6px; }}
    """)
