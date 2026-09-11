import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from database import Database
from ui.window import MainWindow
from ui.manager import QuestionEditor
from ui.profiles import ProfileEditor


APP = QApplication.instance() or QApplication([])
APP.setStyle('Fusion')


class UITest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'ui.db'
        self.db = Database(self.path)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.db.close)
        self.window = MainWindow(self.db, self.path)
        self.window.settings.save({'sound': False, 'music': False})
        self.window.show()
        APP.processEvents()

    def tearDown(self):
        self.window.pages['quiz'].timer.stop()
        self.window.audio.stop()
        self.window.hide()
        self.window.deleteLater()
        APP.processEvents()
        self.db.close()
        self.temp.cleanup()

    def player(self):
        self.window.player_id = self.window.players.save('Test Player', 'Nova')
        self.window.update_player_label()

    def test_all_navigation_and_theme(self):
        self.player()
        for name in ('home', 'players', 'categories', 'difficulty', 'leaderboard', 'achievements', 'manager', 'settings'):
            self.window.navigate(name)
            APP.processEvents()
            self.assertIs(self.window.stack.currentWidget(), self.window.pages[name])
        settings = self.window.pages['settings']
        settings.theme.setCurrentText('Light')
        settings.timed.setChecked(False)
        settings.save()
        self.assertEqual('Light', self.window.settings.get('theme'))
        self.assertFalse(self.window.settings.get('timed'))
        self.window.resize(980, 700)
        APP.processEvents()

    def test_full_round_results_review_and_replay(self):
        self.player()
        self.window.navigate('categories')
        self.window.pages['categories'].choose('Science')
        setup = self.window.pages['difficulty']
        setup.count.setValue(5)
        setup.start.click()
        APP.processEvents()
        quiz = self.window.pages['quiz']
        while not self.window.session.finished:
            session = self.window.session
            index = session.choices.index(session.question.correct)
            QTest.mouseClick(quiz.answer_buttons[index], Qt.MouseButton.LeftButton)
            self.assertTrue(quiz.next.isVisible())
            self.assertTrue(all(not b.isEnabled() for b in quiz.answer_buttons))
            quiz.next.click()
            APP.processEvents()
        self.assertEqual('results', self.window.current_page)
        self.assertEqual(1, self.window.players.stats(self.window.player_id)['played'])
        self.window.open_review(self.window.result_id)
        self.assertEqual(5, self.window.pages['review'].content.count())
        self.window.play_again()
        self.assertEqual('difficulty', self.window.current_page)
        self.assertEqual('Science', self.window.category)

    def test_timeout_and_interruption(self):
        self.player()
        self.window.launch_quiz('Easy', 5)
        quiz = self.window.pages['quiz']
        self.window.session.started -= 31
        quiz.tick()
        self.assertFalse(self.window.session.answers[-1].correct)
        with patch('ui.window.confirm', return_value=False):
            self.window.navigate('home')
        self.assertEqual('quiz', self.window.current_page)
        with patch('ui.window.confirm', return_value=True):
            self.window.navigate('home')
        self.assertIsNone(self.window.session)
        self.assertFalse(quiz.timer.isActive())
        self.assertEqual(0, self.window.players.stats(self.window.player_id)['played'])

    def test_missing_player_and_empty_bank(self):
        self.window.start_setup()
        self.assertEqual('players', self.window.current_page)
        self.player()
        with self.db.connection:
            self.db.connection.execute('DELETE FROM questions')
        self.window.navigate('difficulty')
        self.assertFalse(self.window.pages['difficulty'].start.isEnabled())
        self.window.navigate('manager')
        self.assertEqual(0, self.window.pages['manager'].table.rowCount())

    def test_profile_and_question_editors(self):
        editor = ProfileEditor(self.window)
        editor.name.setText('Grace')
        editor.save()
        self.assertIsNotNone(editor.player_id)
        duplicate = ProfileEditor(self.window)
        duplicate.name.setText('grace')
        duplicate.save()
        self.assertIn('already', duplicate.error.text())
        question = QuestionEditor(self.window)
        question.text.setPlainText('Is this a valid true or false question?')
        question.kind.setCurrentText('True/False')
        question.explanation.setPlainText('This is a complete validation example.')
        question.save()
        self.assertEqual(163, len(self.db.questions()))
        saved = self.db.questions(search='valid true')[0]
        edit = QuestionEditor(self.window, saved)
        edit.correct.setCurrentIndex(1)
        edit.save()
        self.assertEqual('False', self.db.questions(search='valid true')[0].correct)
        self.window.navigate('manager')
        manager = self.window.pages['manager']
        manager.search.setText('valid true')
        self.assertEqual(1, manager.table.rowCount())
        manager.table.selectRow(0)
        with patch('ui.manager.confirm', return_value=True):
            manager.delete()
        self.assertEqual(0, manager.table.rowCount())

    def test_replaced_answer_buttons_are_hidden_immediately(self):
        self.player()
        self.window.launch_quiz('Easy', 5)
        quiz = self.window.pages['quiz']
        previous = list(quiz.answer_buttons)
        quiz.answer(self.window.session.question.correct)
        quiz.advance()
        self.assertTrue(all(widget.isHidden() for widget in previous))

    def test_cancel_exit_keeps_round_and_reset_removes_history(self):
        self.player()
        self.window.launch_quiz('Easy', 1)
        quiz = self.window.pages['quiz']
        with patch('ui.window.confirm', return_value=False):
            self.window.close()
        self.assertIsNotNone(self.window.session)
        self.assertTrue(self.window.isVisible())
        quiz.answer(self.window.session.question.correct)
        quiz.advance()
        self.window.navigate('settings')
        with patch('ui.settings_page.confirm', return_value=True):
            self.window.pages['settings'].reset()
        self.assertEqual(0, self.window.players.stats(self.window.player_id)['played'])
        self.assertFalse(self.window.results.leaderboard())


if __name__ == '__main__':
    unittest.main()
