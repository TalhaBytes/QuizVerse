import random
import time
import uuid
from dataclasses import dataclass

from models.question import Question
from services.scoring import ScoreBreakdown, calculate_score


@dataclass(frozen=True)
class Answer:
    question: Question
    choices: tuple[str, ...]
    selected: str | None
    elapsed: float
    correct: bool
    breakdown: ScoreBreakdown


class QuizSession:
    """One round. Timing uses a monotonic clock, independent of UI timer ticks."""
    def __init__(self, player_id: int, questions: list[Question], category: str,
                 difficulty: str, count: int, time_limit: int, timed: bool,
                 clock=time.monotonic, rng=None):
        if not player_id:
            raise ValueError("Select a player first.")
        if not 1 <= count <= len(questions):
            raise ValueError("There are not enough questions for this round.")
        self.rng = rng or random.Random()
        self.questions = self.rng.sample(questions, count)
        self.player_id, self.category, self.difficulty = player_id, category, difficulty
        self.time_limit, self.timed, self.clock = time_limit, timed, clock
        self.key = uuid.uuid4().hex
        self.answers: list[Answer] = []
        self.score = self.streak = self.best_streak = 0
        self.started = None
        self.choices: tuple[str, ...] = ()

    @property
    def question(self):
        return self.questions[len(self.answers)]

    @property
    def finished(self):
        return len(self.answers) == len(self.questions)

    def begin_question(self):
        if self.finished:
            raise ValueError("This round is complete.")
        if self.started is None:
            self.choices = tuple(self.rng.sample(self.question.answers, len(self.question.answers)))
            self.started = self.clock()
        return self.question

    @property
    def elapsed(self):
        return max(0, self.clock() - self.started) if self.started is not None else 0

    @property
    def remaining(self):
        return max(0, self.time_limit - self.elapsed)

    def submit(self, selected: str | None):
        if self.finished or self.started is None:
            raise ValueError("No question is awaiting an answer.")
        q, elapsed = self.question, self.elapsed
        if selected is not None and selected not in self.choices:
            raise ValueError("Select one of the displayed answers.")
        if self.timed and elapsed >= self.time_limit:
            selected, elapsed = None, float(self.time_limit)
        correct = selected == q.correct
        self.streak = self.streak + 1 if correct else 0
        self.best_streak = max(self.best_streak, self.streak)
        breakdown = calculate_score(correct, self.difficulty, elapsed, self.time_limit, self.streak, self.timed)
        answer = Answer(q, self.choices, selected, elapsed, correct, breakdown)
        self.answers.append(answer)
        self.score += breakdown.total
        self.started = None
        return answer

    def summary(self):
        correct = sum(a.correct for a in self.answers)
        total = len(self.questions)
        percent = correct / total * 100
        return {"score": self.score, "total": total, "correct": correct,
                "incorrect": total - correct, "percentage": percent,
                "streak": self.best_streak,
                "average_time": sum(a.elapsed for a in self.answers) / max(1, len(self.answers)),
                "rating": "Perfect orbit" if percent == 100 else "Stellar work" if percent >= 80 else "Rising star" if percent >= 60 else "Keep exploring"}
