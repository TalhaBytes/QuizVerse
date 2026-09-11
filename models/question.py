from dataclasses import dataclass


DIFFICULTIES = ("Easy", "Medium", "Hard")


@dataclass(frozen=True)
class Question:
    id: int
    category: str
    difficulty: str
    kind: str
    text: str
    answers: tuple[str, ...]
    correct: str
    explanation: str


def validate_question(data: dict) -> dict:
    """Normalize editor/seed data, rejecting incomplete or ambiguous answers."""
    result = {key: str(data.get(key, "")).strip() for key in
              ("category", "difficulty", "kind", "text", "correct", "explanation")}
    answers = data.get("answers", [])
    if not isinstance(answers, (list, tuple)) or not all(isinstance(a, str) for a in answers):
        raise ValueError("Answers must be a list of text choices.")
    result["answers"] = [a.strip() for a in answers]
    if not result["category"] or len(result["category"]) > 60:
        raise ValueError("Enter a category of 1–60 characters.")
    if result["category"].casefold() == "mixed trivia":
        raise ValueError("Mixed Trivia combines categories; choose a specific category.")
    if result["difficulty"] not in DIFFICULTIES:
        raise ValueError("Choose Easy, Medium, or Hard.")
    if result["kind"] not in ("Multiple choice", "True/False"):
        raise ValueError("Choose a valid question type.")
    if not 10 <= len(result["text"]) <= 1000:
        raise ValueError("Question text must contain 10–1,000 characters.")
    if not 5 <= len(result["explanation"]) <= 1500:
        raise ValueError("Add an explanation of 5–1,500 characters.")
    expected = 2 if result["kind"] == "True/False" else 4
    if len(result["answers"]) != expected or any(not a or len(a) > 250 for a in result["answers"]):
        raise ValueError(f"Enter {expected} nonempty answers, each at most 250 characters.")
    if len({a.casefold() for a in result["answers"]}) != expected:
        raise ValueError("Answer choices must be distinct.")
    if result["kind"] == "True/False" and set(result["answers"]) != {"True", "False"}:
        raise ValueError("True/False choices must be True and False.")
    if result["correct"] not in result["answers"]:
        raise ValueError("Select a correct answer from the choices.")
    return result
