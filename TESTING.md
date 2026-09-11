# Verification record

Verified on **2026-09-11**, Windows 11 x64 (build 26200), Python **3.12.10**, PySide6 **6.8.3**, PyInstaller **6.12.0**.

## Automated tests

```powershell
python -m unittest discover -s tests -v
```

**29 tests passed.** Tests use temporary SQLite databases. Expected warning output in two tests reports deliberately missing audio assets and an intentionally malformed question.

Coverage includes:

- All 162 seed questions, category/difficulty coverage, both answer types, uniqueness, and one-time seeding.
- Case-insensitive duplicate player rejection, profile editing, and cascading deletion.
- Question create/edit/delete, filtering/search, duplicate/invalid input rejection, and corrupt-row handling.
- Question sampling without repetition and shuffled answer choices.
- Scoring multipliers, speed/streak bounds, streak resets, expiration at the exact deadline, repeated-submit rejection, and untimed play.
- Complete-only result saving, idempotent saves, transaction rollback on simulated database failure, and retry.
- Accuracy, counts, personal best, achievements and minimum-length thresholds, cumulative 100-question awards.
- Persistent results/reviews/settings across database reopen; settings fallback for corrupt values.
- Review snapshots after original questions are deleted; leaderboard filters; per-player reset.
- Qt navigation, theme/settings controls, profile/question editors, a complete mouse-driven quiz, results/review/replay, timeout, cancellation, empty bank, missing player, and exit cancellation.
- Sound toggles and missing optional audio files; immediate hiding of replaced widgets.

## Native Windows startup and packaging

- Launched the real development entry point with the environment's `python.exe main.py`.
- Launched the generated `QuizVerse.exe` folder distribution.
- Confirmed each displayed a native window titled **QuizVerse · A universe of knowledge**.
- Verified each initialized **162 questions** in its isolated data folder, with SQLite `PRAGMA integrity_check` returning **ok**.
- Both startup checks ran without an application error log entry.
- PyInstaller completed successfully. Its remaining missing-module notices concern conditional/optional standard-library imports for other platforms or unused logging backends.

## Visual inspection

Captured the actual widgets using the Windows Qt platform at normal size (1240 × 850 requested logical pixels) and compact size (980 × 700), with native display scaling.

Inspected home, categories, difficulty setup, quiz, immediate feedback, results, saved reviews, leaderboard, achievements, profiles, Question Manager, editor dialog, and settings. Checked both dark and light appearances and compact layouts. Fixed widget-refresh overlap, light-theme accent contrast, and spin/combo arrow visibility during this pass. Scrollable pages intentionally extend below the viewport when needed.

The README screenshots come from an isolated demonstration profile and automated answers; they are not installed as player records.

## Release acceptance checklist

For a new release or another Windows machine:

1. Extract the full distribution and start the executable without Python installed.
2. Create two players, switch between them, and verify their statistics stay separate.
3. Complete a timed and untimed round; allow one timed question to expire.
4. Review a saved round, restart, and verify it is still available.
5. Add, edit, filter, and delete a custom question/category.
6. Enable/disable music and effects with an audio device connected; verify audible output and volume.
7. Change themes and timer values, save, and restart.
8. Cancel an exit, discard an unfinished round, and reset one player's progress.
9. Check text scaling and keyboard use on the target display.

## Verification boundaries

The executable has been startup-tested on this Windows 11 machine, not on a clean Windows 10/11 installation. Audio loading/toggle behavior is tested; subjective listening quality and every possible device/driver combination are not certified. The executable is unsigned and has no installer. In-progress rounds are intentionally discarded on exit; completed rounds persist.
