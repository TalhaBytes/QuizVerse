ACHIEVEMENTS = (
    ("first", "First Quiz", "Finish your first quiz."),
    ("perfect", "Perfect Score", "Answer every question correctly in a round of at least 5."),
    ("five", "Five Correct in a Row", "Reach a streak of 5 within one round."),
    ("ten", "Ten Correct in a Row", "Reach a streak of 10 within one round."),
    ("science", "Science Expert", "Get at least 80% in a Science round of at least 5."),
    ("history", "History Expert", "Get at least 80% in a History round of at least 5."),
    ("technology", "Technology Expert", "Get at least 80% in a Technology round of at least 5."),
    ("speed", "Speed Master", "Perfect a timed round of at least 5, averaging at most 5 seconds; timer at most 30 seconds."),
    ("hard", "Hard Mode Champion", "Get at least 80% in a Hard round of at least 5."),
    ("hundred", "100 Questions Answered", "Complete 100 questions across saved rounds."),
)


class AchievementService:
    def __init__(self, db):
        self.db = db
        with db.connection:
            db.connection.executemany("INSERT INTO achievements VALUES (?,?,?) ON CONFLICT(code) DO UPDATE SET title=excluded.title,description=excluded.description", ACHIEVEMENTS)

    def all(self, player_id):
        return self.db.connection.execute("""SELECT a.*,p.earned_at FROM achievements a
            LEFT JOIN player_achievements p ON a.code=p.achievement_code AND p.player_id=?
            ORDER BY p.earned_at IS NULL, a.rowid""", (player_id,)).fetchall()

    def unlock(self, session, summary):
        # Called inside the result transaction: awards and statistics commit together.
        eligible = {"first"}
        if summary["streak"] >= 5:
            eligible.add("five")
        if summary["streak"] >= 10:
            eligible.add("ten")
        if summary["total"] >= 5:
            if summary["percentage"] == 100:
                eligible.add("perfect")
                if session.timed and session.time_limit <= 30 and summary["average_time"] <= 5:
                    eligible.add("speed")
            if summary["percentage"] >= 80:
                if session.category in ("Science", "History", "Technology"):
                    eligible.add(session.category.lower())
                if session.difficulty == "Hard":
                    eligible.add("hard")
        answered = self.db.connection.execute("SELECT COALESCE(SUM(total),0) FROM quiz_results WHERE player_id=?", (session.player_id,)).fetchone()[0]
        if answered >= 100:
            eligible.add("hundred")
        unlocked = []
        for code, title, _ in ACHIEVEMENTS:
            if code in eligible:
                cursor = self.db.connection.execute("INSERT OR IGNORE INTO player_achievements(player_id,achievement_code) VALUES (?,?)", (session.player_id, code))
                if cursor.rowcount:
                    unlocked.append(title)
        return unlocked
