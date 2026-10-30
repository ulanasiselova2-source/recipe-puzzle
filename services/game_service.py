def is_answer_correct(selected: list[str], correct: list[str]) -> bool:
    return set(selected) == set(correct)


def calculate_level(xp: int) -> int:
    return max(1, xp // 50 + 1)
