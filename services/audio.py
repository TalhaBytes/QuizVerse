import logging

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QSoundEffect

from utils.paths import resource_path


class AudioService(QObject):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings, self.effects = settings, {}
        for name in ("correct", "incorrect", "finish", "ambient"):
            path = resource_path(f"assets/sounds/{name}.wav")
            if not path.exists():
                logging.warning("Optional sound missing: %s", path.name)
                continue
            effect = QSoundEffect(self)
            effect.setSource(QUrl.fromLocalFile(str(path)))
            effect.setVolume(0.12 if name == "ambient" else 0.3)
            if name == "ambient":
                effect.setLoopCount(QSoundEffect.Loop.Infinite.value)
            self.effects[name] = effect
        self.refresh()

    def refresh(self):
        music = self.effects.get("ambient")
        if music:
            if self.settings.get("music"):
                if not music.isPlaying():
                    music.play()
            else:
                music.stop()

    def play(self, name):
        if self.settings.get("sound") and name in self.effects:
            self.effects[name].play()

    def stop(self):
        for effect in self.effects.values():
            effect.stop()
