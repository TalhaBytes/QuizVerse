import random
import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import Database
from services.players import PlayerService
from services.quiz import QuizSession
from services.settings import SettingsService
from services.scoring import calculate_score
from services.achievements import AchievementService
from services.leaderboard import ResultService


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class ServicesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'test.db'
        self.db = Database(self.path)
        self.players = PlayerService(self.db)
        self.player = self.players.save('Ada')
        self.achievements = AchievementService(self.db)
        self.results = ResultService(self.db, self.achievements)
        self.clock = Clock()

    def tearDown(self):
        self.db.close()
        self.temp.cleanup()

    def session(self, count=5, category='Science', difficulty='Easy', timed=True):
        return QuizSession(self.player, self.db.questions(category, difficulty), category, difficulty,
                           count, 30, timed, self.clock, random.Random(12))

    def finish(self, session, seconds=2, wrong_at=()):
        while not session.finished:
            q = session.begin_question()
            self.clock.now += seconds
            selected = next(a for a in q.answers if a != q.correct) if len(session.answers) in wrong_at else q.correct
            session.submit(selected)
        return session

    def test_bank_coverage_and_uniqueness(self):
        questions = self.db.questions()
        self.assertEqual(162, len(questions))
        self.assertEqual(162, len({q.text.casefold() for q in questions}))
        self.assertEqual(9, len(self.db.categories()))
        for category in self.db.categories():
            for difficulty in ('Easy', 'Medium', 'Hard'):
                subset = self.db.questions(category, difficulty)
                self.assertEqual(6, len(subset))
                self.assertEqual({'Multiple choice', 'True/False'}, {q.kind for q in subset})

    def test_seed_is_not_repeated_after_restart(self):
        self.db.delete_question(self.db.questions()[0].id)
        self.db.close()
        self.db = Database(self.path)
        self.assertEqual(161, len(self.db.questions()))

    def test_duplicate_player_normalizes_case_and_spaces(self):
        with self.assertRaises(ValueError):
            self.players.save('  ADA  ')
        with self.assertRaises(ValueError):
            self.players.save(' ')
        self.players.save('Ada Lovelace', 'Nova', self.player)
        self.assertEqual('Nova', self.players.get(self.player)['avatar'])

    def test_question_crud_search_filter_and_validation(self):
        data = dict(category='Custom', difficulty='Hard', kind='Multiple choice', text='What is two plus three?',
                    answers=['5', '6', '7', '8'], correct='5', explanation='Two and three sum to five.')
        key = self.db.save_question(data)
        self.assertEqual(1, len(self.db.questions('Custom', 'Hard', 'plus')))
        with self.assertRaises(ValueError):
            self.db.save_question(data)
        data['text'] = 'What is three plus two?'
        self.db.save_question(data, key)
        self.assertEqual(data['text'], self.db.questions('Custom')[0].text)
        data['answers'] = ['5', '5', '7', '8']
        with self.assertRaises(ValueError):
            self.db.save_question(data)
        self.db.delete_question(key)
        self.assertFalse(self.db.questions('Custom'))

    def test_malformed_question_is_skipped(self):
        with self.db.connection:
            self.db.connection.execute("UPDATE questions SET answers='invalid json' WHERE id=1")
        self.assertEqual(161, len(self.db.questions()))

    def test_empty_bank_and_missing_player(self):
        with self.assertRaises(ValueError):
            QuizSession(self.player, [], 'Science', 'Easy', 1, 30, True)
        with self.assertRaises(ValueError):
            QuizSession(0, self.db.questions(), 'Mixed Trivia', 'Easy', 1, 30, True)

    def test_random_questions_and_answer_order(self):
        s = self.session()
        self.assertEqual(5, len({q.id for q in s.questions}))
        original_order = [q.id for q in self.db.questions('Science', 'Easy')][:5]
        self.assertNotEqual(original_order, [q.id for q in s.questions])
        orders = []
        while not s.finished:
            q = s.begin_question()
            orders.append(s.choices != q.answers)
            self.assertEqual(set(q.answers), set(s.choices))
            s.submit(q.correct)
        self.assertTrue(any(orders))

    def test_timeout_and_double_submission(self):
        s = self.session()
        q = s.begin_question()
        self.clock.now += 30
        answer = s.submit(q.correct)
        self.assertFalse(answer.correct)
        self.assertIsNone(answer.selected)
        self.assertEqual(30, answer.elapsed)
        with self.assertRaises(ValueError):
            s.submit(q.correct)

    def test_untimed_has_no_deadline_or_speed_bonus(self):
        s = self.session(timed=False)
        q = s.begin_question()
        self.clock.now += 100
        a = s.submit(q.correct)
        self.assertTrue(a.correct)
        self.assertEqual(0, a.breakdown.speed)

    def test_scoring_boundaries_and_streak_cap(self):
        self.assertEqual(0, calculate_score(False, 'Hard', 0, 15, 10, True).total)
        self.assertEqual(450, calculate_score(True, 'Hard', 0, 15, 1, True).total)
        self.assertEqual(200, calculate_score(True, 'Easy', 30, 30, 99, True).total)
        self.assertEqual(300, calculate_score(True, 'Hard', 5, 15, 1, False).total)

    def test_streak_resets_and_statistics(self):
        s = self.finish(self.session(count=6), wrong_at=(3,))
        summary = s.summary()
        self.assertEqual(3, summary['streak'])
        self.assertEqual(5, summary['correct'])
        self.results.save(s)
        stats = self.players.stats(self.player)
        self.assertEqual((1, 6, 5, 1), (stats['played'], stats['answered'], stats['correct'], stats['incorrect']))
        self.assertAlmostEqual(100 * 5/6, stats['accuracy'])
        self.assertEqual(s.score, stats['highest'])

    def test_atomic_save_and_idempotence(self):
        s = self.finish(self.session())
        result_id, awards = self.results.save(s)
        same_id, second_awards = self.results.save(s)
        self.assertEqual(result_id, same_id)
        self.assertFalse(second_awards)
        self.assertEqual(5, len(self.results.answers(result_id)))
        self.assertIn('Science Expert', awards)
        self.assertIn('Speed Master', awards)
        self.assertEqual(1, self.players.stats(self.player)['played'])

    def test_transaction_rolls_back_on_award_failure(self):
        s = self.finish(self.session())
        from unittest.mock import patch
        with patch.object(self.achievements, 'unlock', side_effect=sqlite3.OperationalError('test failure')):
            with self.assertRaises(sqlite3.OperationalError):
                self.results.save(s)
        self.assertEqual(0, self.players.stats(self.player)['played'])
        self.assertEqual(0, self.db.connection.execute('SELECT COUNT(*) FROM quiz_answers').fetchone()[0])
        self.results.save(s)
        self.assertEqual(1, self.players.stats(self.player)['played'])

    def test_incomplete_quiz_cannot_be_saved(self):
        with self.assertRaises(ValueError):
            self.results.save(self.session())

    def test_reviews_survive_question_edits_and_deletion(self):
        s = self.finish(self.session())
        key, _ = self.results.save(s)
        first = self.results.answers(key)[0]['question_text']
        self.db.delete_question(s.questions[0].id)
        self.assertEqual(first, self.results.answers(key)[0]['question_text'])

    def test_achievement_thresholds_and_persistence(self):
        s = self.finish(self.session(count=1))
        _, awards = self.results.save(s)
        self.assertEqual(['First Quiz'], awards)
        for _ in range(10):
            self.results.save(self.finish(self.session(count=10, category='Mixed Trivia', difficulty='Hard')))
        earned = {a['code'] for a in self.achievements.all(self.player) if a['earned_at']}
        self.assertTrue({'hundred', 'ten', 'hard', 'perfect'} <= earned)

    def test_leaderboard_filters(self):
        self.results.save(self.finish(self.session()))
        self.results.save(self.finish(self.session(category='History', timed=False)))
        self.assertEqual(1, len(self.results.leaderboard(category='History', mode='Practice', count=5)))
        self.assertFalse(self.results.leaderboard(difficulty='Hard'))

    def test_reset_and_delete_cascade(self):
        self.results.save(self.finish(self.session()))
        self.players.reset_stats(self.player)
        self.assertEqual(0, self.players.stats(self.player)['played'])
        self.assertFalse(any(a['earned_at'] for a in self.achievements.all(self.player)))
        self.assertEqual(0, self.db.connection.execute('SELECT COUNT(*) FROM quiz_answers').fetchone()[0])
        self.assertEqual(162, len(self.db.questions()))
        self.results.save(self.finish(self.session()))
        self.players.delete(self.player)
        self.assertFalse(self.results.leaderboard())
        self.assertEqual([], self.db.connection.execute('PRAGMA foreign_key_check').fetchall())

    def test_settings_persist_and_corrupt_values_fall_back(self):
        settings = SettingsService(self.db)
        settings.save({'theme': 'Light', 'timed': False, 'Hard': 45})
        self.db.close()
        self.db = Database(self.path)
        settings = SettingsService(self.db)
        self.assertEqual('Light', settings.get('theme'))
        self.assertFalse(settings.get('timed'))
        self.assertEqual(45, settings.get('Hard'))
        with self.db.connection:
            self.db.connection.execute("UPDATE settings SET value='9999' WHERE key='Hard'")
            self.db.connection.execute("UPDATE settings SET value='invalid' WHERE key='theme'")
        self.assertEqual(15, settings.get('Hard'))
        self.assertEqual('Dark', settings.get('theme'))

    def test_results_survive_restart(self):
        key, _ = self.results.save(self.finish(self.session()))
        self.db.close()
        self.db = Database(self.path)
        self.assertEqual(5, len(ResultService(self.db, AchievementService(self.db)).answers(key)))
        self.assertEqual(1, PlayerService(self.db).stats(self.player)['played'])


if __name__ == '__main__':
    unittest.main()
