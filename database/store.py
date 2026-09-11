import json
import logging
import sqlite3
from pathlib import Path

from models.question import Question, validate_question
from utils.paths import resource_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS players (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE,
 avatar TEXT NOT NULL DEFAULT 'Orbit', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS questions (
 id INTEGER PRIMARY KEY, category TEXT NOT NULL, difficulty TEXT NOT NULL
 CHECK(difficulty IN ('Easy','Medium','Hard')), kind TEXT NOT NULL,
 text TEXT NOT NULL, text_key TEXT NOT NULL UNIQUE, answers TEXT NOT NULL,
 correct TEXT NOT NULL, explanation TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS quiz_results (
 id INTEGER PRIMARY KEY, session_key TEXT NOT NULL UNIQUE,
 player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
 category TEXT NOT NULL, difficulty TEXT NOT NULL, total INTEGER NOT NULL,
 correct INTEGER NOT NULL, score INTEGER NOT NULL, best_streak INTEGER NOT NULL,
 average_time REAL NOT NULL, timed INTEGER NOT NULL, time_limit INTEGER NOT NULL,
 completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS quiz_answers (
 id INTEGER PRIMARY KEY, result_id INTEGER NOT NULL REFERENCES quiz_results(id) ON DELETE CASCADE,
 position INTEGER NOT NULL, question_text TEXT NOT NULL, category TEXT NOT NULL,
 choices TEXT NOT NULL, selected TEXT, correct_answer TEXT NOT NULL,
 explanation TEXT NOT NULL, response_time REAL NOT NULL, points INTEGER NOT NULL,
 is_correct INTEGER NOT NULL, UNIQUE(result_id, position)
);
CREATE TABLE IF NOT EXISTS achievements (
 code TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS player_achievements (
 player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
 achievement_code TEXT NOT NULL REFERENCES achievements(code),
 earned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY(player_id, achievement_code)
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS questions_filter ON questions(category, difficulty);
CREATE INDEX IF NOT EXISTS results_player ON quiz_results(player_id);
PRAGMA user_version = 1;
"""


class Database:
    def __init__(self, path: str | Path):
        self.connection = sqlite3.connect(str(path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            self.connection.close()
            raise ValueError("This database belongs to a newer QuizVerse version.")
        self.connection.executescript(SCHEMA)
        if not self.connection.execute("SELECT 1 FROM settings WHERE key='seeded'").fetchone():
            self.seed()

    def seed(self):
        bank = json.loads(resource_path("data/questions.json").read_text(encoding="utf-8"))
        with self.connection:
            for entry in bank:
                self.save_question(entry, commit=False)
            self.connection.execute("INSERT INTO settings VALUES ('seeded', 'true')")

    def save_question(self, entry: dict, question_id: int | None = None, *, commit=True):
        q = validate_question(entry)
        values = (q["category"], q["difficulty"], q["kind"], q["text"],
                  " ".join(q["text"].casefold().split()), json.dumps(q["answers"]), q["correct"], q["explanation"])
        try:
            if question_id is None:
                cursor = self.connection.execute("INSERT INTO questions(category,difficulty,kind,text,text_key,answers,correct,explanation) VALUES (?,?,?,?,?,?,?,?)", values)
            else:
                cursor = self.connection.execute("UPDATE questions SET category=?,difficulty=?,kind=?,text=?,text_key=?,answers=?,correct=?,explanation=? WHERE id=?", (*values, question_id))
            if commit:
                self.connection.commit()
            return question_id or cursor.lastrowid
        except sqlite3.IntegrityError as exc:
            if commit:
                self.connection.rollback()
            raise ValueError("A question with that text already exists.") from exc

    def questions(self, category="All", difficulty="All", search="") -> list[Question]:
        sql, args = "SELECT * FROM questions WHERE 1=1", []
        if category not in ("All", "Mixed Trivia"):
            sql += " AND category=?"
            args.append(category)
        if difficulty != "All":
            sql += " AND difficulty=?"
            args.append(difficulty)
        if search:
            sql += " AND instr(lower(text), lower(?)) > 0"
            args.append(search)
        results = []
        for row in self.connection.execute(sql + " ORDER BY category, id", args):
            try:
                data = dict(row)
                data["answers"] = json.loads(data["answers"])
                q = validate_question(data)
                results.append(Question(row["id"], q["category"], q["difficulty"], q["kind"], q["text"], tuple(q["answers"]), q["correct"], q["explanation"]))
            except (ValueError, TypeError):
                logging.warning("Skipped invalid question row %s", row["id"])
        return results

    def categories(self):
        return sorted({q.category for q in self.questions()})

    def delete_question(self, question_id: int):
        with self.connection:
            self.connection.execute("DELETE FROM questions WHERE id=?", (question_id,))

    def close(self):
        self.connection.close()
