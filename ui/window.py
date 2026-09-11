import logging
import sqlite3

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                               QStackedWidget, QApplication, QMessageBox)

from services.players import PlayerService
from services.settings import SettingsService
from services.achievements import AchievementService
from services.leaderboard import ResultService
from services.quiz import QuizSession
from services.audio import AudioService
from ui.components import label, button, confirm, avatar_icon, row
from ui.theme import apply_theme
from ui.home import HomePage
from ui.profiles import ProfilesPage
from ui.setup import CategoryPage, DifficultyPage
from ui.game import QuizPage, ResultsPage, ReviewPage
from ui.records import LeaderboardPage, AchievementsPage
from ui.manager import ManagerPage
from ui.settings_page import SettingsPage
from utils.paths import resource_path


class MainWindow(QMainWindow):
    def __init__(self, db, database_path):
        super().__init__()
        self.db, self.database_path = db, database_path
        self.players, self.settings = PlayerService(db), SettingsService(db)
        self.achievements = AchievementService(db)
        self.results = ResultService(db, self.achievements)
        self.player_id = None
        self.session = None
        self.result_id = self.review_id = None
        self.unlocked = []
        self.category = "Mixed Trivia"
        self.confirming = False
        self.current_page = "home"
        self.setWindowTitle("QuizVerse · A universe of knowledge")
        self.setWindowIcon(QIcon(str(resource_path("assets/icons/quizverse.svg"))))
        self.resize(1240, 850)
        self.setMinimumSize(980, 700)
        self.audio = AudioService(self.settings, self)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(232)
        nav_layout = QVBoxLayout(sidebar)
        nav_layout.setContentsMargins(18, 28, 18, 22)
        nav_layout.setSpacing(8)
        nav_layout.addWidget(label("✦ QuizVerse", "brand"))
        nav_layout.addWidget(label("A UNIVERSE OF KNOWLEDGE", "eyebrow"))
        nav_layout.addSpacing(30)
        self.nav = {}
        for name, title in (("home", "⌂   Home"), ("players", "◉   Players"), ("categories", "▷   Play quiz"),
                            ("leaderboard", "≡   Leaderboard"), ("achievements", "✦   Achievements"),
                            ("manager", "▤   Question Manager"), ("settings", "⚙   Settings")):
            widget = button(title, lambda checked=False, n=name: self.start_setup() if n == "categories" else self.navigate(n))
            widget.setObjectName("nav")
            widget.setCheckable(True)
            self.nav[name] = widget
            nav_layout.addWidget(widget)
        nav_layout.addStretch()
        self.player_label = label("No player selected", "section")
        self.avatar_label = label("")
        self.avatar_label.setFixedWidth(38)
        self.avatar_label.hide()
        nav_layout.addLayout(row(self.avatar_label, self.player_label))
        nav_layout.addWidget(label("●  Offline & ready", "muted"))
        nav_layout.addWidget(button("Exit", self.close))
        layout.addWidget(sidebar)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.pages = {"home": HomePage(self), "players": ProfilesPage(self), "categories": CategoryPage(self),
                      "difficulty": DifficultyPage(self), "quiz": QuizPage(self), "results": ResultsPage(self),
                      "review": ReviewPage(self), "leaderboard": LeaderboardPage(self),
                      "achievements": AchievementsPage(self), "manager": ManagerPage(self), "settings": SettingsPage(self)}
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.apply_settings()
        self.navigate("home")

    def current_player(self):
        return self.players.get(self.player_id) if self.player_id else None

    def update_player_label(self):
        player = self.current_player()
        self.player_label.setText(f'{player["name"]}\n{player["avatar"]} badge' if player else "No player selected")
        self.avatar_label.setVisible(player is not None)
        if player:
            self.avatar_label.setPixmap(avatar_icon(player["avatar"]).pixmap(36, 36))

    def apply_settings(self):
        apply_theme(QApplication.instance(), self.settings.get("theme"))
        self.audio.refresh()

    def can_leave(self):
        if self.current_page != "quiz" or not self.session:
            return True
        if self.session.finished:
            return self.save_completed()
        self.confirming = True
        try:
            leave = confirm(self, "Leave this quiz?", "This round is unfinished. Leave and discard its progress? Completed rounds are already saved.")
        finally:
            self.confirming = False
        if leave:
            self.pages["quiz"].timer.stop()
            self.session = None
        else:
            self.pages["quiz"].tick()
        return leave

    def navigate(self, name, **kwargs):
        if name != self.current_page and not self.can_leave():
            self.update_nav()
            return
        if name in ("results", "quiz") and self.session is None:
            name = "home"
        self.current_page = name
        page = self.pages[name]
        page.refresh(**kwargs)
        self.stack.setCurrentWidget(page)
        self.update_nav()

    def update_nav(self):
        active = "categories" if self.current_page in ("difficulty", "quiz", "results") else self.current_page
        for name, widget in self.nav.items():
            widget.setChecked(name == active)

    def start_setup(self):
        if not self.current_player():
            self.navigate("players")
        else:
            self.navigate("categories")

    def launch_quiz(self, difficulty, count):
        if not self.current_player():
            self.navigate("players")
            return
        try:
            questions = self.db.questions(self.category, difficulty)
            self.session = QuizSession(self.player_id, questions, self.category, difficulty, count,
                                       self.settings.get(difficulty), self.settings.get("timed"))
            self.result_id, self.unlocked = None, []
            self.navigate("quiz")
        except ValueError as exc:
            QMessageBox.warning(self, "Unable to start quiz", str(exc))

    def save_completed(self):
        if self.result_id:
            return True
        try:
            self.result_id, self.unlocked = self.results.save(self.session)
            return True
        except (sqlite3.Error, OSError) as exc:
            logging.exception("Unable to save completed quiz")
            QMessageBox.warning(self, "Round not saved", f"Could not save this round: {exc}\nFree disk space or close other instances, then select See your results to retry. Keep the app open to retain this round.")
            return False

    def play_again(self):
        if self.session:
            self.category = self.session.category
            self.pages["difficulty"].difficulty.setCurrentText(self.session.difficulty)
        self.navigate("difficulty")

    def open_review(self, result_id):
        self.review_id = result_id
        self.navigate("review")

    def closeEvent(self, event):
        unfinished = self.current_page == "quiz" and self.session and not self.session.finished
        if unfinished:
            allowed = self.can_leave()
        else:
            allowed = self.can_leave() and confirm(self, "Exit QuizVerse?", "Close QuizVerse? Your completed rounds and saved settings are safe.")
        if not allowed:
            event.ignore()
            return
        self.pages["quiz"].timer.stop()
        self.audio.stop()
        self.db.close()
        event.accept()
