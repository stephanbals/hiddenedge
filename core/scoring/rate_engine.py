# =========================================
# AIJobHunter V4 - Rate Engine v2
# Engagement-aware pricing
# =========================================

def evaluate_rate(fit, opportunity, strategy, win, engagement_type="FREELANCE"):

    # =========================================
    # NON-FREELANCE → NO RATE
    # =========================================

    if engagement_type != "FREELANCE":
        return {
            "rate_range": "N/A",
            "rate_positioning": "N/A",
            "negotiation_advice": "Salary-based role – rate not applicable",
            "rate_factors": [f"Engagement type: {engagement_type}"]
        }

    # =========================================
    # FREELANCE LOGIC
    # =========================================

    level = fit.get("level_match", "MATCHED")
    opp_score = opportunity.get("opportunity_score", 0)
    win_prob = win.get("win_probability", 0)
    strat = strategy.get("strategy", "")

    base = 650

    if level == "OVERQUALIFIED":
        base += 100
    elif level == "UNDERQUALIFIED":
        base -= 100

    if opp_score >= 70:
        base += 100
    elif opp_score < 45:
        base -= 100

    if win_prob >= 70:
        base += 50
    elif win_prob < 40:
        base -= 50

    if strat == "NEGOTIATE":
        base += 100

    base = max(400, min(1200, base))

    low = int(base * 0.9)
    high = int(base * 1.15)

    return {
        "rate_range": f"€{low}–€{high}/day",
        "rate_positioning": "MARKET",
        "negotiation_advice": "Align rate with role expectations",
        "rate_factors": [
            f"Opportunity: {opp_score}",
            f"Win probability: {win_prob}",
            f"Level: {level}"
        ]
    }