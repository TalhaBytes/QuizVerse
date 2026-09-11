from dataclasses import dataclass


MULTIPLIERS = {"Easy": 1, "Medium": 2, "Hard": 3}


@dataclass(frozen=True)
class ScoreBreakdown:
    base: int = 0
    speed: int = 0
    streak: int = 0

    @property
    def total(self) -> int:
        return self.base + self.speed + self.streak


def calculate_score(correct: bool, difficulty: str, elapsed: float,
                    time_limit: int, streak: int, timed: bool) -> ScoreBreakdown:
    multiplier = MULTIPLIERS[difficulty]
    if not correct:
        return ScoreBreakdown()
    base = 100 * multiplier
    remaining = max(0.0, min(1.0, 1 - elapsed / max(1, time_limit)))
    speed = int(50 * multiplier * remaining) if timed else 0
    return ScoreBreakdown(base, speed, min(max(0, streak - 1), 10) * 10 * multiplier)
