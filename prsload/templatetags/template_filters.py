RED1 = "#dc2626"
ORANGE1 = "#ea580c"
ORANGE2 = "#f97316"
ORANGE3 = "#f59e0b"
YELLOW1 = "#facc15"
YELLOW2 = "#fde047"
BLUE1 = "#22d3ee"
BLUE2 = "#2dd4bf"
GREEN1 = "#34d399"
GREEN2 = "#10b981"
GREEN3 = "#16a34a"

ALL_COLORS = [
    RED1,
    ORANGE1,
    ORANGE2,
    ORANGE3,
    YELLOW1,
    YELLOW2,
    BLUE1,
    BLUE2,
    GREEN1,
    GREEN2,
    GREEN3,
]


def choose_color_for_review_time(value: float):
    if value >= 50:
        return GREEN3
    if value >= 45:
        return GREEN2
    if value >= 40:
        return GREEN1
    if value >= 35:
        return BLUE2
    if value >= 30:
        return BLUE1
    if value >= 25:
        return YELLOW2
    if value >= 20:
        return YELLOW1
    if value >= 15:
        return ORANGE3
    if value >= 10:
        return ORANGE2
    if value >= 5:
        return ORANGE1
    return RED1


def choose_color_for_missing_reviews(value: float):
    if value >= 90:
        return RED1
    if value >= 85:
        return ORANGE1
    if value >= 80:
        return ORANGE2
    if value >= 73:
        return ORANGE3
    if value >= 66:
        return YELLOW1
    if value >= 59:
        return YELLOW2
    if value >= 52:
        return BLUE1
    if value >= 45:
        return BLUE2
    if value >= 38:
        return GREEN1
    if value >= 31:
        return GREEN2
    return GREEN3
