from PySide6.QtWidgets import QComboBox, QCheckBox, QSpinBox, QFormLayout

from models.question import DIFFICULTIES
from ui.components import Page, label, card, button, confirm


class SettingsPage(Page):
    def __init__(self, window):
        super().__init__("Set your own pace", "Make QuizVerse feel right for you. Changes apply to your next round.")
        self.window = window
        frame, layout = card()
        form = QFormLayout()
        form.setSpacing(16)
        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light"])
        self.sound, self.music, self.timed = QCheckBox("Answer and result sounds"), QCheckBox("Quiet ambient loop"), QCheckBox("Enable question countdown")
        self.count = QSpinBox()
        self.count.setRange(1, 50)
        form.addRow("Appearance", self.theme)
        form.addRow("Sound effects", self.sound)
        form.addRow("Background music", self.music)
        form.addRow("Timed quizzes", self.timed)
        form.addRow("Preferred round length", self.count)
        self.timers = {}
        for level in DIFFICULTIES:
            spin = QSpinBox()
            spin.setRange(5, 120)
            spin.setSuffix(" seconds")
            self.timers[level] = spin
            form.addRow(f"{level} timer", spin)
        layout.addLayout(form)
        self.body.addWidget(frame)
        self.body.addWidget(button("Save settings", self.save, True))
        self.status = label("", "muted")
        self.body.addWidget(self.status)
        reset, layout = card()
        layout.addWidget(label("Reset player progress", "section"))
        layout.addWidget(label("Delete completed rounds, leaderboard entries, and achievements for the currently selected player. Your question bank and other players are kept.", "muted"))
        self.reset_button = button("Reset selected player's statistics", self.reset)
        self.reset_button.setObjectName("danger")
        layout.addWidget(self.reset_button)
        self.body.addWidget(reset)
        self.body.addWidget(label(f"Local database: {window.database_path}", "muted"))
        self.body.addStretch()

    def refresh(self):
        settings = self.window.settings
        self.theme.setCurrentText(settings.get("theme"))
        self.sound.setChecked(settings.get("sound"))
        self.music.setChecked(settings.get("music"))
        self.timed.setChecked(settings.get("timed"))
        self.count.setValue(settings.get("count"))
        for level, spin in self.timers.items():
            spin.setValue(settings.get(level))
        self.reset_button.setEnabled(self.window.current_player() is not None)
        self.status.setText("")

    def save(self):
        values = {"theme": self.theme.currentText(), "sound": self.sound.isChecked(),
                  "music": self.music.isChecked(), "timed": self.timed.isChecked(), "count": self.count.value()}
        values.update({level: spin.value() for level, spin in self.timers.items()})
        self.window.settings.save(values)
        self.window.apply_settings()
        self.status.setText("Settings saved. Your next quiz will use these preferences.")

    def reset(self):
        player = self.window.current_player()
        if player and confirm(self, "Reset statistics?", f'Reset all statistics, saved reviews, and achievements for {player["name"]}? This cannot be undone.'):
            self.window.players.reset_stats(player["id"])
            self.window.session = None
            self.window.result_id = None
            self.status.setText(f'Progress reset for {player["name"]}.')
