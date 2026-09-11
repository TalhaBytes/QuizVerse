import os
import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / relative


def data_directory() -> Path:
    override = os.environ.get("QUIZVERSE_DATA_DIR")
    path = Path(override) if override else Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local/share")) / "QuizVerse"
    path.mkdir(parents=True, exist_ok=True)
    return path
