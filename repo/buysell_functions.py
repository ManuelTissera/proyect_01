

def analyze_reversal_after_streak(streaks, target_streak):
    reversals = []

    for i in range(len(streaks) - 1):
        current = streaks[i]
        next_streak = streaks[i + 1]

        if current == target_streak:
            reversals.append(abs(next_streak))  # Medimos cuánto dura la reversión

    return reversals


def summarize_reversals(reversals):
    if not reversals:
        return 0
    return sum(reversals) / len(reversals)


def classify_reversal_durations(reversals):
    less_than_3 = sum(1 for r in reversals if r < 3)
    equal_to_3 = sum(1 for r in reversals if r == 3)
    greater_than_3 = sum(1 for r in reversals if r > 3)
    greater_than_2 = sum(1 for r in reversals if r > 2)
    total = len(reversals)
    if total == 0:
        return 0, 0, 0, 0
    return (less_than_3 / total) * 100, (equal_to_3 / total) * 100, (greater_than_3 / total) * 100, (greater_than_2 / total) * 100
