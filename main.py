"""Launch QuizVerse with `python main.py` (Python 3.12)."""
import logging
from logging.handlers import RotatingFileHandler
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from database import Database
from ui.window import MainWindow
from utils.paths import data_directory


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("QuizVerse")
    app.setOrganizationName("QuizVerse")
    app.setStyle("Fusion")
    try:
        directory = data_directory()
        logging.basicConfig(level=logging.INFO, handlers=[RotatingFileHandler(
            directory / "quizverse.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")],
            format="%(asctime)s %(levelname)s %(message)s")
        db = Database(directory / "quizverse.db")
        window = MainWindow(db, directory / "quizverse.db")
    except Exception as exc:
        logging.exception("Startup failed")
        QMessageBox.critical(None, "QuizVerse could not start", f"The local database or required app files could not be opened.\n\n{exc}\n\nCheck that the application data folder is writable. Existing data has not been reset.")
        return 1

    def handle_exception(kind, value, traceback):
        logging.error("Unhandled application error", exc_info=(kind, value, traceback))
        QMessageBox.critical(window, "Something went wrong", f"The operation could not be completed.\n{value}\n\nYour saved data is retained. Check quizverse.log in the application data folder for details.")

    sys.excepthook = handle_exception
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
