"""Rebuild the original icon and synthesized, royalty-free sound assets."""
import math
import struct
import wave
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]


def sound(name, notes, note_length, volume):
    sample_rate = 22050
    samples = bytearray()
    for frequencies in notes:
        for index in range(int(sample_rate * note_length)):
            t = index / sample_rate
            fade = min(1, t / 0.04, (note_length - t) / 0.15)
            value = sum(math.sin(2 * math.pi * f * t) for f in frequencies) / len(frequencies)
            samples.extend(struct.pack('<h', int(32767 * volume * max(0, fade) * value)))
    with wave.open(str(ROOT / f'assets/sounds/{name}.wav'), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(samples)


if __name__ == '__main__':
    app = QApplication([])
    icon = QIcon(str(ROOT / 'assets/icons/quizverse.svg'))
    if not icon.pixmap(128, 128).save(str(ROOT / 'assets/icons/quizverse.ico')):
        raise RuntimeError('Icon export failed')
    sound('correct', [(523.25,), (659.25,), (783.99,)], .14, .45)
    sound('incorrect', [(293.66,), (220.,)], .18, .35)
    sound('finish', [(523.25,), (659.25,), (783.99,), (523.25, 659.25, 783.99)], .22, .4)
    sound('ambient', [(130.81, 164.81, 196.), (110., 130.81, 164.81),
                      (87.31, 130.81, 174.61), (98., 146.83, 196.)], 3, .3)
