if __name__ == "__main__":
    print("HiddenEdge Engine v1.0 | SB3PM")
# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
#
# This code is proprietary and confidential.
# Unauthorized use, distribution, or replication is prohibited.
# =========================================

# =========================================
# GAP ENGINE — STANDARDIZED INTERFACE
# =========================================

import re


def normalize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def evaluate_gaps(cv_text: str, job_text: str):

    cv_tokens = set(normalize(cv_text))
    job_tokens = set(normalize(job_text))

    missing = job_tokens - cv_tokens

    critical = []
    moderate = []
    minor = []

    # SIMPLE HEURISTIC (FAST + WORKS)

    for word in list(missing)[:20]:

        if len(word) < 4:
            continue

        if word in ["sap", "data", "ai", "cloud", "program", "portfolio"]:
            critical.append({
                "type": "skill",
                "message": f"Missing core skill: {word}"
            })

        elif word in ["analysis", "reporting", "stakeholder", "governance"]:
            moderate.append({
                "type": "skill",
                "message": f"Missing supporting skill: {word}"
            })

        else:
            minor.append({
                "type": "skill",
                "message": f"Nice-to-have skill: {word}"
            })

    deal_breaker = len(critical) >= 2

    return {
        "critical": critical,
        "moderate": moderate,
        "minor": minor,
        "deal_breaker": deal_breaker
    }