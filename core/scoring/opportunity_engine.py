# =========================================
# OPPORTUNITY ENGINE — STABLE CLEAN VERSION
# =========================================

def evaluate_opportunity(fit_result, gap_result):

    fit = fit_result.get("fit_score", 0)

    critical_gaps = gap_result.get("critical", [])
    moderate_gaps = gap_result.get("moderate", [])

    # BASE SCORE (0–10)
    score = (fit / 100) * 6

    # penalties (soft)
    score -= len(critical_gaps) * 1.0
    score -= len(moderate_gaps) * 0.3

    score = max(0, min(10, score))

    # DECISION
    if fit >= 65:
        decision = "APPLY"
    elif fit >= 45:
        decision = "MAYBE"
    else:
        decision = "IGNORE"

    return {
        "score": round(score, 2),
        "decision": decision
    }