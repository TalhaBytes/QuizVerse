import json


DEFAULTS = {"theme": "Dark", "sound": True, "music": False, "timed": True,
            "Easy": 30, "Medium": 20, "Hard": 15, "count": 5}


class SettingsService:
    def __init__(self, db):
        self.db = db

    def get(self, key):
        default = DEFAULTS[key]
        row = self.db.connection.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        try:
            value = json.loads(row[0]) if row else default
            if type(value) is not type(default):
                return default
            if key == "theme" and value not in ("Dark", "Light"):
                return default
            if key in ("Easy", "Medium", "Hard") and not 5 <= value <= 120:
                return default
            if key == "count" and not 1 <= value <= 50:
                return default
            return value
        except (ValueError, TypeError):
            return default

    def save(self, values):
        with self.db.connection:
            for key, value in values.items():
                if key in DEFAULTS:
                    self.db.connection.execute("INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value)))
