from PySide6.QtWidgets import QWidget, QVBoxLayout

from ui.components import Page, OrbitArt, label, card, row, metric, button, clear


class HomePage(Page):
    def __init__(self, window):
        super().__init__("Your next discovery starts here.", "A little curiosity. A new challenge. A universe of knowledge.")
        self.window = window
        hero, layout = card()
        content = QWidget()
        text = QVBoxLayout(content)
        text.setSpacing(16)
        text.addWidget(label("WELCOME TO QUIZVERSE", "eyebrow"))
        text.addWidget(label("Big questions.\nBrighter minds.", "heroTitle"))
        text.addWidget(label("Pick your universe, beat the clock, and turn what you know into your next personal best.", "muted"))
        text.addWidget(button("Start a quiz  →", lambda: window.navigate("players", for_play=True), True))
        layout.addLayout(row(content, OrbitArt()))
        self.body.addWidget(hero)
        self.stats = QVBoxLayout()
        self.body.addLayout(self.stats)
        self.body.addWidget(label("Make it your kind of challenge", "section"))
        self.body.addLayout(row(button("Explore categories", lambda: window.start_setup()),
                                button("View leaderboard", lambda: window.navigate("leaderboard")),
                                button("Your achievements", lambda: window.navigate("achievements"))))
        self.body.addWidget(label("OFFLINE BY DESIGN  •  No accounts, ads, or internet required", "eyebrow"))
        self.body.addStretch()

    def refresh(self):
        clear(self.stats)
        player = self.window.current_player()
        stats = self.window.players.stats(player["id"]) if player else {"played": 0, "highest": 0}
        self.stats.addLayout(row(metric("Questions to discover", str(len(self.window.db.questions()))),
                                metric("Quizzes completed", str(stats["played"])),
                                metric("Personal best" if player else "Choose a player to begin", f'{stats["highest"]:,}')))
