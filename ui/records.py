from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QSpinBox, QTableWidgetItem, QGridLayout, QMessageBox

from models.question import DIFFICULTIES
from ui.components import Page, label, row, table, button, clear, card


class LeaderboardPage(Page):
    def __init__(self, window):
        super().__init__("The local legends", "Your best rounds, saved on this device. Select a round to review its answers.")
        self.window = window
        self.category, self.difficulty, self.mode = QComboBox(), QComboBox(), QComboBox()
        self.category.addItem("All")
        self.difficulty.addItems(["All", *DIFFICULTIES])
        self.mode.addItems(["All", "Timed", "Practice"])
        self.count = QSpinBox()
        self.count.setRange(0, 50)
        self.count.setSpecialValueText("Any length")
        self.count.setSuffix(" questions")
        self.category.setAccessibleName("Filter category")
        self.difficulty.setAccessibleName("Filter difficulty")
        self.mode.setAccessibleName("Filter timing mode")
        self.count.setAccessibleName("Filter number of questions")
        self.body.addLayout(row(self.category, self.difficulty, self.mode, self.count))
        self.table = table(["#", "Player", "Score", "Accuracy", "Length", "Category", "Level", "Timer", "Date (UTC)"])
        self.body.addWidget(self.table)
        self.empty = label("", "muted")
        self.body.addWidget(self.empty)
        self.body.addWidget(button("Review selected round", self.review, True))
        self.body.addWidget(label("Ranked by total points, then accuracy, then response time. Longer rounds and different timers affect scores; use filters and the Timer column when comparing.", "muted"))
        self.body.addStretch()
        for combo in (self.category, self.difficulty, self.mode):
            combo.currentTextChanged.connect(self.load)
        self.count.valueChanged.connect(self.load)
        self.table.cellDoubleClicked.connect(lambda r, c: self.review())

    def refresh(self):
        previous = self.category.currentText()
        # Include historical categories even after questions are deleted.
        historical = [r[0] for r in self.window.db.connection.execute("SELECT DISTINCT category FROM quiz_results")]
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItems(["All"] + sorted(set(self.window.db.categories() + historical + ["Mixed Trivia"])))
        self.category.setCurrentText(previous)
        self.category.blockSignals(False)
        self.load()

    def load(self):
        rows = self.window.results.leaderboard(self.category.currentText(), self.difficulty.currentText(), self.mode.currentText(), self.count.value())
        self.table.setRowCount(len(rows))
        for index, r in enumerate(rows):
            values = [index + 1, r["name"], f'{r["score"]:,}', f'{100*r["correct"]/r["total"]:.1f}%', r["total"], r["category"], r["difficulty"], f'{r["time_limit"]}s' if r["timed"] else "Practice", r["completed_at"]]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, r["id"])
                self.table.setItem(index, col, item)
        self.empty.setText(f"{len(rows)} rounds shown · Top 100" if rows else "No rounds yet for these filters. Finish a quiz to set the first score.")

    def review(self):
        index = self.table.currentRow()
        if index < 0:
            QMessageBox.information(self, "Select a round", "Select a saved round first.")
        else:
            self.window.open_review(self.table.item(index, 0).data(Qt.ItemDataRole.UserRole))


class AchievementsPage(Page):
    def __init__(self, window):
        super().__init__("Small wins. Stellar milestones.", "Keep exploring to fill your collection. Every award is earned through play.")
        self.window = window
        self.player = label("", "section")
        self.body.addWidget(self.player)
        self.body.addWidget(button("Choose player", lambda: window.navigate("players")))
        self.grid = QGridLayout()
        self.grid.setSpacing(14)
        self.body.addLayout(self.grid)
        self.body.addStretch()

    def refresh(self):
        clear(self.grid)
        player = self.window.current_player()
        self.player.setText(player["name"] if player else "Select a player to track your collection.")
        for index, a in enumerate(self.window.achievements.all(self.window.player_id)):
            frame, layout = card()
            layout.addWidget(label("✦  UNLOCKED" if a["earned_at"] else "◇  LOCKED", "eyebrow"))
            layout.addWidget(label(a["title"], "section"))
            layout.addWidget(label(a["description"], "muted"))
            if a["earned_at"]:
                layout.addWidget(label(f'Earned {a["earned_at"]} UTC', "muted"))
            self.grid.addWidget(frame, index // 2, index % 2)
