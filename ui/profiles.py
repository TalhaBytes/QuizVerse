from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QLineEdit, QComboBox,
                               QDialog, QDialogButtonBox, QFormLayout, QVBoxLayout, QMessageBox)

from services.players import AVATARS
from ui.components import Page, label, row, metric, clear, button, confirm, avatar_icon


class ProfileEditor(QDialog):
    def __init__(self, parent, player=None):
        super().__init__(parent)
        self.setWindowTitle("Edit player" if player else "Create player")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name = QLineEdit(player["name"] if player else "")
        self.name.setMaxLength(30)
        self.name.setPlaceholderText("Your player name")
        self.avatar = QComboBox()
        self.avatar.addItems(AVATARS)
        if player:
            self.avatar.setCurrentText(player["avatar"])
        form.addRow("Player name", self.name)
        form.addRow("Avatar badge", self.avatar)
        layout.addLayout(form)
        self.error = label("", "muted")
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.window, self.player = parent, player
        self.player_id = None

    def save(self):
        try:
            self.player_id = self.window.players.save(self.name.text(), self.avatar.currentText(), self.player["id"] if self.player else None)
            self.accept()
        except ValueError as exc:
            self.error.setText(str(exc))


class ProfilesPage(Page):
    def __init__(self, window):
        super().__init__("Who's playing?", "Keep your progress, personal records, and achievements in one place.")
        self.window = window
        self.list = QListWidget()
        self.list.setMinimumHeight(180)
        self.list.setIconSize(QSize(36, 36))
        self.list.currentItemChanged.connect(self.select)
        self.body.addWidget(self.list)
        self.body.addLayout(row(button("New player", self.create, True), button("Edit selected", self.edit), button("Delete selected", self.delete)))
        self.status = label("", "section")
        self.body.addWidget(self.status)
        self.stats = QVBoxLayout()
        self.body.addLayout(self.stats)
        self.body.addWidget(button("Continue to categories  →", self.continue_play, True))
        self.body.addStretch()

    def refresh(self, **kwargs):
        self.list.blockSignals(True)
        self.list.clear()
        for player in self.window.players.all():
            item = QListWidgetItem(avatar_icon(player["avatar"]), f'{player["name"]}    ·    {player["avatar"]}')
            item.setData(Qt.ItemDataRole.UserRole, player["id"])
            self.list.addItem(item)
            if player["id"] == self.window.player_id:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self.show_stats()

    def select(self, current, previous):
        if current:
            self.window.player_id = current.data(Qt.ItemDataRole.UserRole)
            self.window.update_player_label()
        self.show_stats()

    def show_stats(self):
        clear(self.stats)
        player = self.window.current_player()
        if not player:
            self.status.setText("Create or select a player to begin.")
            return
        s = self.window.players.stats(player["id"])
        earned = sum(bool(a["earned_at"]) for a in self.window.achievements.all(player["id"]))
        self.status.setText(f'{player["name"]} · {player["avatar"]} badge')
        self.stats.addLayout(row(metric("Quizzes played", s["played"]), metric("Questions answered", s["answered"]), metric("Accuracy", f'{s["accuracy"]:.1f}%')))
        self.stats.addLayout(row(metric("Correct / incorrect", f'{s["correct"]} / {s["incorrect"]}'), metric("Highest / average score", f'{s["highest"]:,} / {s["average"]:,.0f}'), metric("Best streak / awards", f'{s["streak"]} / {earned}')))

    def create(self):
        editor = ProfileEditor(self.window)
        if editor.exec():
            self.window.player_id = editor.player_id
            self.window.update_player_label()
            self.refresh()

    def edit(self):
        player = self.window.current_player()
        if player:
            if ProfileEditor(self.window, player).exec():
                self.window.update_player_label()
                self.refresh()
        else:
            QMessageBox.information(self, "Choose a player", "Select a player to edit.")

    def delete(self):
        player = self.window.current_player()
        if player and confirm(self, "Delete player?", f'Delete {player["name"]} and all their results and achievements? This cannot be undone.'):
            self.window.players.delete(player["id"])
            self.window.player_id = None
            self.window.update_player_label()
            self.refresh()

    def continue_play(self):
        self.window.start_setup()
