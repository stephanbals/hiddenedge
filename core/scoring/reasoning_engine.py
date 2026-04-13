# =========================================
# REASONING ENGINE — CLEAR DECISION EXPLAINER
# =========================================

def build_reasoning(fit_result, gap_result, opportunity_result):

    fit = fit_result.get("fit_score", 0)
    decision = opportunity_result.get("decision")

    critical = gap_result.get("critical", [])
    moderate = gap_result.get("moderate", [])

    parts = []

    # =========================================
    # DECISION FIRST (IMPORTANT)
    # =========================================

    if decision == "APPLY":
        parts.append("🔥 Strong candidate — worth applying")
    elif decision == "MAYBE":
        parts.append("⚠ Viable but needs positioning")
    else:
        parts.append("❌ Low probability based on current profile")

    # =========================================
    # WHY
    # =========================================

    parts.append(f"Fit score: {fit}")

    if critical:
        parts.append(f"Key gap: {critical[0]['message']}")
    elif moderate:
        parts.append(f"Gap: {moderate[0]['message']}")

    # =========================================
    # STRATEGY
    # =========================================

    if decision == "APPLY":
        parts.append("Strategy: Position as direct match")
    elif decision == "MAYBE":
        parts.append("Strategy: Emphasize transferable experience")
    else:
        parts.append("Strategy: Only apply if limited alternatives")

    return " | ".join(parts)