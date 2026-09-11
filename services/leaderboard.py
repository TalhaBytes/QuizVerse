import json


class ResultService:
    def __init__(self, db, achievements):
        self.db, self.achievements = db, achievements

    def save(self, session):
        if not session.finished:
            raise ValueError("Only completed quizzes can be saved.")
        existing = self.db.connection.execute("SELECT id FROM quiz_results WHERE session_key=?", (session.key,)).fetchone()
        if existing:
            return existing[0], []
        s = session.summary()
        with self.db.connection:
            cursor = self.db.connection.execute("""INSERT INTO quiz_results
                (session_key,player_id,category,difficulty,total,correct,score,best_streak,average_time,timed,time_limit)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (session.key, session.player_id, session.category, session.difficulty,
                s["total"], s["correct"], s["score"], s["streak"], s["average_time"], session.timed, session.time_limit))
            result_id = cursor.lastrowid
            for position, a in enumerate(session.answers, 1):
                self.db.connection.execute("""INSERT INTO quiz_answers
                    (result_id,position,question_text,category,choices,selected,correct_answer,explanation,response_time,points,is_correct)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (result_id, position, a.question.text, a.question.category,
                    json.dumps(a.choices), a.selected, a.question.correct, a.question.explanation, a.elapsed, a.breakdown.total, a.correct))
            unlocked = self.achievements.unlock(session, s)
        return result_id, unlocked

    def leaderboard(self, category="All", difficulty="All", mode="All", count=0):
        query = "SELECT r.*,p.name FROM quiz_results r JOIN players p ON p.id=r.player_id WHERE 1=1"
        args = []
        for field, value in (("category", category), ("difficulty", difficulty)):
            if value != "All":
                query += f" AND r.{field}=?"
                args.append(value)
        if mode != "All":
            query += " AND r.timed=?"
            args.append(mode == "Timed")
        if count:
            query += " AND r.total=?"
            args.append(count)
        return self.db.connection.execute(query + " ORDER BY r.score DESC, r.correct * 1.0 / r.total DESC, r.average_time ASC, r.id ASC LIMIT 100", args).fetchall()

    def answers(self, result_id):
        return self.db.connection.execute("SELECT * FROM quiz_answers WHERE result_id=? ORDER BY position", (result_id,)).fetchall()
