from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
                               QComboBox, QDialogButtonBox, QTableWidgetItem, QMessageBox,
                               QHeaderView)

from models.question import DIFFICULTIES
from ui.components import Page, label, row, button, table, confirm


class QuestionEditor(QDialog):
    def __init__(self, parent, question=None):
        super().__init__(parent)
        self.window, self.question = parent, question
        self.setWindowTitle("Edit question" if question else "Add question")
        self.resize(670, 710)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)
        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(parent.db.categories())
        self.category.setCurrentText(question.category if question else "General Knowledge")
        self.difficulty = QComboBox()
        self.difficulty.addItems(DIFFICULTIES)
        self.kind = QComboBox()
        self.kind.addItems(["Multiple choice", "True/False"])
        self.text = QTextEdit()
        self.text.setAcceptRichText(False)
        self.text.setMaximumHeight(100)
        self.text.setPlaceholderText("Write a clear, unambiguous question (10–1,000 characters).")
        self.answers = [QLineEdit() for _ in range(4)]
        self.correct = QComboBox()
        self.correct.addItems(["Answer 1", "Answer 2", "Answer 3", "Answer 4"])
        self.explanation = QTextEdit()
        self.explanation.setAcceptRichText(False)
        self.explanation.setMaximumHeight(100)
        self.explanation.setPlaceholderText("Explain the correct answer (5–1,500 characters).")
        form.addRow("Category (or type a new one)", self.category)
        form.addRow("Difficulty", self.difficulty)
        form.addRow("Type", self.kind)
        form.addRow("Question", self.text)
        for i, widget in enumerate(self.answers):
            widget.setMaxLength(250)
            form.addRow(f"Answer {i + 1}", widget)
        form.addRow("Correct choice", self.correct)
        form.addRow("Explanation", self.explanation)
        layout.addLayout(form)
        self.error = label("", "muted")
        layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.kind.currentTextChanged.connect(self.update_kind)
        if question:
            self.difficulty.setCurrentText(question.difficulty)
            self.kind.setCurrentText(question.kind)
            self.text.setPlainText(question.text)
            for widget, answer in zip(self.answers, question.answers):
                widget.setText(answer)
            self.correct.setCurrentIndex(question.answers.index(question.correct))
            self.explanation.setPlainText(question.explanation)
        self.update_kind()
        if question and question.kind == "True/False":
            self.correct.setCurrentIndex(0 if question.correct == "True" else 1)

    def update_kind(self):
        is_tf = self.kind.currentText() == "True/False"
        selected = self.correct.currentIndex()
        self.correct.clear()
        self.correct.addItems(["Answer 1", "Answer 2"] if is_tf else ["Answer 1", "Answer 2", "Answer 3", "Answer 4"])
        self.correct.setCurrentIndex(max(0, min(selected, self.correct.count() - 1)))
        for index, widget in enumerate(self.answers):
            widget.setEnabled(not is_tf)
            if is_tf:
                widget.setText(["True", "False", "", ""][index])

    def save(self):
        size = 2 if self.kind.currentText() == "True/False" else 4
        answers = [w.text() for w in self.answers[:size]]
        data = {"category": self.category.currentText(), "difficulty": self.difficulty.currentText(),
                "kind": self.kind.currentText(), "text": self.text.toPlainText(),
                "answers": answers, "correct": answers[self.correct.currentIndex()],
                "explanation": self.explanation.toPlainText()}
        try:
            self.window.db.save_question(data, self.question.id if self.question else None)
            self.accept()
        except ValueError as exc:
            self.error.setText(str(exc))


class ManagerPage(Page):
    def __init__(self, window):
        super().__init__("Your question collection", "Create a fresh challenge. Add, refine, or remove questions in your local library.")
        self.window = window
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search question text…")
        self.category = QComboBox()
        self.category.addItem("All")
        self.category.setAccessibleName("Filter category")
        self.difficulty = QComboBox()
        self.difficulty.addItems(["All", *DIFFICULTIES])
        self.difficulty.setAccessibleName("Filter difficulty")
        self.body.addLayout(row(self.search, self.category, self.difficulty))
        self.table = table(["Question", "Category", "Difficulty", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setMinimumHeight(360)
        self.body.addWidget(self.table)
        self.status = label("", "muted")
        self.body.addWidget(self.status)
        self.body.addLayout(row(button("Add question", self.add, True), button("Edit selected", self.edit), button("Delete selected", self.delete)))
        self.body.addWidget(label("New categories can be typed in the editor. Changes affect future quizzes; saved reviews retain the original question and answer.", "muted"))
        self.body.addStretch()
        self.search.textChanged.connect(self.load)
        self.category.currentTextChanged.connect(self.load)
        self.difficulty.currentTextChanged.connect(self.load)
        self.table.cellDoubleClicked.connect(lambda r, c: self.edit())
        self.questions = []

    def refresh(self):
        category = self.category.currentText()
        self.category.blockSignals(True)
        self.category.clear()
        self.category.addItems(["All"] + self.window.db.categories())
        self.category.setCurrentText(category)
        self.category.blockSignals(False)
        self.load()

    def load(self):
        self.questions = self.window.db.questions(self.category.currentText(), self.difficulty.currentText(), self.search.text())
        self.table.setRowCount(len(self.questions))
        for index, q in enumerate(self.questions):
            for col, value in enumerate((q.text, q.category, q.difficulty, q.kind)):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.table.setItem(index, col, item)
        self.status.setText(f"{len(self.questions)} matching questions" if self.questions else "No matching valid questions. Adjust filters or add a question.")

    def selected(self):
        index = self.table.currentRow()
        if index < 0:
            QMessageBox.information(self, "Choose a question", "Select a question first.")
            return None
        return self.questions[index]

    def add(self):
        if QuestionEditor(self.window).exec():
            self.refresh()

    def edit(self):
        q = self.selected()
        if q and QuestionEditor(self.window, q).exec():
            self.refresh()

    def delete(self):
        q = self.selected()
        if q and confirm(self, "Delete question?", f"Permanently remove this question?\n\n{q.text}\n\nSaved answer reviews will be kept."):
            self.window.db.delete_question(q.id)
            self.refresh()
