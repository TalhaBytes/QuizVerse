import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from services.audio import AudioService


APP = QApplication.instance() or QApplication([])


class TestSettings:
    __test__ = False

    def get(self, key):
        return False


class AudioTest(unittest.TestCase):
    def test_missing_optional_assets_are_nonfatal(self):
        with patch('services.audio.resource_path', return_value=Path('/nonexistent-quizverse-assets/audio.wav')):
            audio = AudioService(TestSettings())
            self.assertEqual({}, audio.effects)
            audio.play('correct')
            audio.refresh()
            audio.stop()

    def test_sounds_exist_and_music_can_be_toggled(self):
        audio = AudioService(TestSettings())
        self.assertEqual({'correct', 'incorrect', 'finish', 'ambient'}, set(audio.effects))
        self.assertEqual(-2, audio.effects['ambient'].loopCount())
        self.assertFalse(audio.effects['ambient'].isPlaying())
        with patch.object(audio.settings, 'get', return_value=True):
            audio.refresh()
            audio.play('correct')
        audio.stop()
        self.assertTrue(all(not effect.isPlaying() for effect in audio.effects.values()))
