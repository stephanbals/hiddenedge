# =========================================
# HiddenEdge – DECISION ENGINE v1
# =========================================

def make_decision(fit_score, opportunity_score, gap_result):

    deal_breaker = gap_result.get("deal_breaker", False)

    # =========================================
    # DECISION LOGIC
    # =========================================

    if deal_breaker:
        decision = "IGNORE"

    elif opportunity_score >= 7.5 and fit_score >= 70:
        decision = "APPLY"

    elif opportunity_score >= 5.5:
        decision = "MAYBE"

    else:
        decision = "IGNORE"

    # =========================================
    # CONFIDENCE
    # =========================================

    if decision == "APPLY":
        confidence = "HIGH"
    elif decision == "MAYBE":
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    # =========================================
    # REASONING
    # =========================================

    if decision == "IGNORE":
        reasoning = "Low fit or critical gaps reduce success probability"

    elif decision == "MAYBE":
        reasoning = "Moderate fit with some gaps — possible but uncertain"

    else:
        reasoning = "Strong fit and low risk — high probability of success"

    return {
        "decision": decision,
        "confidence": confidence,
        "reasoning": reasoning
    }