"""Harm label taxonomy. The classifier (services/classify) writes scores for these labels.

Each label should trace to a harm in docs/background.md. Add a label here first, then teach the
classifier to score it; rankers and the UI read labels from this list.
"""
HARM_LABELS: dict[str, str] = {
    "body_image": "Promotes appearance ideals, whitening, extreme dieting or cosmetic pressure",
    "dangerous_activity": "Stunts, challenges or acts that risk injury if imitated",
    "violence": "Fighting, weapons, threats or graphic harm",
    "gambling": "Betting, lotteries, get-rich-quick or speculative finance",
    "sexualized": "Sexualized framing of people, especially appearance-focused content",
}

# A video whose max label score is at or above this counts as "flagged" (metrics, filtering).
FLAG_THRESHOLD = 0.5
