# Build from the repository root: python -m PyInstaller --clean QuizVerse.spec
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / 'main.py')], pathex=[str(root)],
    binaries=[], datas=[(str(root / 'data'), 'data'),
                        (str(root / 'assets/icons'), 'assets/icons'),
                        (str(root / 'assets/sounds'), 'assets/sounds')],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtQml'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='QuizVerse',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, icon=str(root / 'assets/icons/quizverse.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='QuizVerse')
