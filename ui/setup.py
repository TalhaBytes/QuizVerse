from PySide6.QtWidgets import QGridLayout, QComboBox, QSpinBox, QFormLayout

from models.question import DIFFICULTIES
from ui.components import Page, label, button, card, clear


CATEGORY_NOTES = {
    "Mixed Trivia": ("✦", "A little of everything"), "General Knowledge": ("◎", "Everyday wonders"),
    "Science": ("⚛", "Explore how things work"), "Technology": ("⌁", "Ideas that change the world"),
    "Computers": ("⌘", "Bits, bytes, and beyond"), "History": ("◷", "Stories through time"),
    "Geography": ("◇", "Discover our planet"), "Sports": ("⚑", "Records, rules, and rivals"),
    "Movies & Entertainment": ("▷", "From screen to stage"), "Literature": ("≡", "A world of words")}


class CategoryPage(Page):
    def __init__(self, window):
        super().__init__("Choose your universe", "01  PLAYER     →     02  CATEGORY     →     03  CHALLENGE")
        self.window = window
        self.grid = QGridLayout()
        self.grid.setSpacing(16)
        self.body.addLayout(self.grid)
        self.body.addStretch()

    def refresh(self):
        clear(self.grid)
        categories = ["Mixed Trivia"] + self.window.db.categories()
        for index, category in enumerate(categories):
            icon, description = CATEGORY_NOTES.get(category, ("✧", "A new world to explore"))
            frame, layout = card()
            layout.addWidget(label(f"{icon}   {category}", "section"))
            layout.addWidget(label(description, "muted"))
            count = len(self.window.db.questions(category))
            layout.addWidget(button(f"{count} questions   →", lambda checked=False, c=category: self.choose(c)))
            self.grid.addWidget(frame, index // 2, index % 2)

    def choose(self, category):
        self.window.category = category
        self.window.navigate("difficulty")


class DifficultyPage(Page):
    def __init__(self, window):
        super().__init__("Make it a challenge", "01  PLAYER     →     02  CATEGORY     →     03  CHALLENGE")
        self.window = window
        self.heading = label("", "section")
        self.body.addWidget(self.heading)
        frame, layout = card()
        form = QFormLayout()
        form.setSpacing(18)
        self.difficulty = QComboBox()
        self.difficulty.addItems(DIFFICULTIES)
        self.difficulty.currentTextChanged.connect(self.update_availability)
        self.count = QSpinBox()
        self.count.setRange(1, 50)
        form.addRow("Difficulty", self.difficulty)
        form.addRow("Number of questions", self.count)
        layout.addLayout(form)
        self.details = label("", "muted")
        layout.addWidget(self.details)
        layout.addWidget(label("SCORING", "eyebrow"))
        layout.addWidget(label("100 base points × difficulty (1× / 2× / 3×). Timed answers earn up to 50 × difficulty in speed bonus. Each consecutive correct answer adds 10 × difficulty, capped after 10 bonus steps.", "muted"))
        self.start = button("Launch quiz  →", self.launch, True)
        layout.addWidget(self.start)
        layout.addWidget(button("Change category", lambda: window.navigate("categories")))
        self.body.addWidget(frame)
        self.body.addWidget(label("Take your time: disable the timer in Settings for a practice round. Practice rounds earn no speed bonus.", "muted"))
        self.body.addStretch()

    def refresh(self):
        self.heading.setText(self.window.category)
        self.update_availability()
        self.count.setValue(min(self.count.maximum(), self.window.settings.get("count")))

    def update_availability(self):
        level = self.difficulty.currentText()
        available = len(self.window.db.questions(self.window.category, level))
        self.count.setRange(1, max(1, min(50, available)))
        self.start.setEnabled(available > 0)
        timing = f'{self.window.settings.get(level)} seconds per question' if self.window.settings.get("timed") else "Untimed practice"
        self.details.setText(f"{available} questions available · {timing}\n" + ("Question count is limited to available unique questions." if available else "No valid questions here yet. Add some in Question Manager."))

    def launch(self):
        self.window.launch_quiz(self.difficulty.currentText(), self.count.value())
