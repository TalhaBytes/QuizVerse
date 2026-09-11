import sqlite3


AVATARS = ("Orbit", "Nova", "Comet", "Lunar", "Solar", "Cosmos")


class PlayerService:
    def __init__(self, db):
        self.db = db

    def all(self):
        return self.db.connection.execute("SELECT * FROM players ORDER BY name COLLATE NOCASE").fetchall()

    def get(self, player_id):
        return self.db.connection.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()

    def save(self, name, avatar="Orbit", player_id=None):
        name = " ".join(name.split())
        if not 1 <= len(name) <= 30:
            raise ValueError("Use a player name of 1–30 characters.")
        if avatar not in AVATARS:
            raise ValueError("Choose an available avatar.")
        try:
            with self.db.connection:
                if player_id:
                    self.db.connection.execute("UPDATE players SET name=?,name_key=?,avatar=? WHERE id=?", (name, name.casefold(), avatar, player_id))
                    return player_id
                return self.db.connection.execute("INSERT INTO players(name,name_key,avatar) VALUES (?,?,?)", (name, name.casefold(), avatar)).lastrowid
        except sqlite3.IntegrityError as exc:
            raise ValueError("That player name is already in use.") from exc

    def delete(self, player_id):
        with self.db.connection:
            self.db.connection.execute("DELETE FROM players WHERE id=?", (player_id,))

    def stats(self, player_id):
        row = self.db.connection.execute("""SELECT COUNT(*) AS played, COALESCE(SUM(total),0) AS answered,
            COALESCE(SUM(correct),0) AS correct, COALESCE(MAX(score),0) AS highest,
            COALESCE(AVG(score),0) AS average, COALESCE(MAX(best_streak),0) AS streak
            FROM quiz_results WHERE player_id=?""", (player_id,)).fetchone()
        stats = dict(row)
        stats["incorrect"] = stats["answered"] - stats["correct"]
        stats["accuracy"] = 100 * stats["correct"] / stats["answered"] if stats["answered"] else 0
        return stats

    def reset_stats(self, player_id):
        with self.db.connection:
            self.db.connection.execute("DELETE FROM quiz_results WHERE player_id=?", (player_id,))
            self.db.connection.execute("DELETE FROM player_achievements WHERE player_id=?", (player_id,))
