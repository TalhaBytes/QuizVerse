import math

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QProgressBar

from ui.components import Page, label, row, button, card, metric, clear


class AnswerButton(QPushButton):
    def __init__(self, text, action):
        super().__init__()
        self.setObjectName("choice")
        self.setAccessibleName(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        self.caption = label(text)
        self.caption.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(self.caption)
        self.clicked.connect(action)
        self.setMinimumHeight(70)


class QuizPage(Page):
    def __init__(self, window):
        super().__init__("In your element", "Stay curious. Every answer is a chance to learn.")
        self.window = window
        self.session = None
        self.answer_buttons = []
        self.meta = label("", "eyebrow")
        self.body.addWidget(self.meta)
        self.score = label("", "section")
        self.time = label("", "section")
        self.body.addLayout(row(self.score, self.time))
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.body.addWidget(self.progress)
        frame, layout = card()
        self.question = label("", "section")
        self.question.setMinimumHeight(64)
        layout.addWidget(self.question)
        self.choices_layout = QVBoxLayout()
        self.choices_layout.setSpacing(12)
        layout.addLayout(self.choices_layout)
        self.feedback = label("")
        layout.addWidget(self.feedback)
        self.next = button("Next question  →", self.advance, True)
        self.next.hide()
        layout.addWidget(self.next)
        self.body.addWidget(frame)
        self.body.addWidget(label("Keyboard: 1–4 to answer · Enter for the next question · Leave quiz to end an unfinished round", "muted"))
        self.body.addWidget(button("Leave quiz", lambda: window.navigate("home")))
        self.body.addStretch()
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.tick)
        self.shortcuts = []
        for i in range(4):
            shortcut = QShortcut(QKeySequence(str(i + 1)), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda index=i: self.keyboard_answer(index))
            self.shortcuts.append(shortcut)
        shortcut = QShortcut(QKeySequence("Return"), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(lambda: self.advance() if self.next.isVisible() else None)
        self.shortcuts.append(shortcut)

    def refresh(self):
        self.session = self.window.session
        self.show_question()

    def show_question(self):
        clear(self.choices_layout)
        self.answer_buttons = []
        s = self.session
        q = s.begin_question()
        self.meta.setText(f"QUESTION {len(s.answers) + 1} OF {len(s.questions)}   /   {q.category.upper()}   /   {s.difficulty.upper()}")
        self.question.setText(q.text)
        self.progress.setRange(0, len(s.questions))
        self.progress.setValue(len(s.answers))
        self.feedback.hide()
        self.next.hide()
        for index, choice in enumerate(s.choices):
            widget = AnswerButton(f"{index + 1}    {choice}", lambda checked=False, a=choice: self.answer(a))
            self.answer_buttons.append(widget)
            self.choices_layout.addWidget(widget)
        self.update_score()
        self.timer.start()
        self.tick()
        self.verticalScrollBar().setValue(0)
        self.answer_buttons[0].setFocus()

    def update_score(self):
        self.score.setText(f"{self.session.score:,} points    ·    {self.session.streak} streak")

    def tick(self):
        if not self.session or self.session.started is None or self.window.confirming:
            return
        if self.session.timed:
            self.time.setText(f"◷  {math.ceil(self.session.remaining)}s remaining")
            if self.session.remaining <= 0:
                self.answer(None)
        else:
            self.time.setText(f"Practice  ·  {int(self.session.elapsed)}s elapsed")

    def keyboard_answer(self, index):
        if index < len(self.answer_buttons) and self.answer_buttons[index].isEnabled():
            self.answer_buttons[index].click()

    def answer(self, selected):
        if self.session.started is None:
            return
        self.timer.stop()
        a = self.session.submit(selected)
        for widget, choice in zip(self.answer_buttons, a.choices):
            widget.setEnabled(False)
            if choice == a.question.correct:
                widget.setObjectName("correct")
                widget.caption.setText(widget.caption.text() + "   ✓ Correct")
            elif choice == a.selected:
                widget.setObjectName("incorrect")
                widget.caption.setText(widget.caption.text() + "   × Your answer")
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        b = a.breakdown
        message = f"Correct! +{b.total} points ({b.base} base + {b.speed} speed + {b.streak} streak)" if a.correct else "Time's up." if a.selected is None else "Not quite."
        self.feedback.setText(f"{message}\n{a.question.explanation}")
        self.feedback.show()
        self.time.setText(f"Answered in {a.elapsed:.1f}s")
        self.progress.setValue(len(self.session.answers))
        self.update_score()
        self.window.audio.play("correct" if a.correct else "incorrect")
        self.next.setText("See your results  →" if self.session.finished else "Next question  →")
        self.next.show()
        self.next.setFocus()
        if self.session.finished:
            self.window.save_completed()

    def advance(self):
        if self.session.started is not None:
            return
        if self.session.finished:
            if self.window.save_completed():
                self.window.audio.play("finish")
                self.window.navigate("results")
        else:
            self.show_question()


class ResultsPage(Page):
    def __init__(self, window):
        super().__init__("Round complete", "One more discovery. One step further.")
        self.window = window
        self.content = QVBoxLayout()
        self.body.addLayout(self.content)
        self.body.addLayout(row(button("Play again", window.play_again, True),
                                button("Review answers", lambda: window.open_review(window.result_id)),
                                button("Leaderboard", lambda: window.navigate("leaderboard")),
                                button("Home", lambda: window.navigate("home"))))
        self.body.addStretch()

    def refresh(self):
        clear(self.content)
        session = self.window.session
        s = session.summary()
        hero, layout = card()
        layout.addWidget(label(s["rating"].upper(), "eyebrow"))
        layout.addWidget(label(f'{s["score"]:,} points', "heroTitle"))
        layout.addWidget(label(f'{session.category} · {session.difficulty} · {s["total"]} questions · ' + (f'Timed ({session.time_limit}s)' if session.timed else 'Untimed practice'), "muted"))
        self.content.addWidget(hero)
        self.content.addLayout(row(metric("Accuracy", f'{s["percentage"]:.1f}%'), metric("Correct / incorrect", f'{s["correct"]} / {s["incorrect"]}'), metric("Best streak", s["streak"]), metric("Average response", f'{s["average_time"]:.1f}s')))
        if self.window.unlocked:
            self.content.addWidget(label("ACHIEVEMENTS UNLOCKED", "eyebrow"))
            self.content.addWidget(label("  ·  ".join(self.window.unlocked), "section"))
        self.content.addWidget(label("Your completed round and answer review have been saved locally.", "muted"))


class ReviewPage(Page):
    def __init__(self, window):
        super().__init__("Every answer tells a story", "Revisit your choices and learn the why behind each answer.")
        self.window = window
        self.body.addWidget(button("Back to leaderboard", lambda: window.navigate("leaderboard")))
        self.content = QVBoxLayout()
        self.body.addLayout(self.content)
        self.body.addStretch()

    def refresh(self):
        clear(self.content)
        answers = self.window.results.answers(self.window.review_id)
        if not answers:
            self.content.addWidget(label("This round has no saved answers."))
        for a in answers:
            frame, layout = card()
            layout.addWidget(label(f'{a["position"]:02d}   {"✓ CORRECT" if a["is_correct"] else "× INCORRECT"}   ·   {a["points"]} points   ·   {a["response_time"]:.1f}s', "eyebrow"))
            layout.addWidget(label(a["question_text"], "section"))
            layout.addWidget(label(f'Your answer: {a["selected"] or "No answer (time expired)"}\nCorrect answer: {a["correct_answer"]}'))
            layout.addWidget(label(a["explanation"], "muted"))
            self.content.addWidget(frame)
