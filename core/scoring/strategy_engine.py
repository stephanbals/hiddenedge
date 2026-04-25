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
# AIJobHunter V4 - Strategy Engine v3
# Engagement-aware strategy
# =========================================

def evaluate_strategy(fit_result, gap_result, opportunity_result, engagement_type="FREELANCE"):

    score = opportunity_result.get("opportunity_score", 0)
    domain_mismatch = gap_result.get("domain_mismatch", "NONE")

    # =========================================
    # HARD STOP
    # =========================================

    if domain_mismatch == "CRITICAL":
        return {
            "strategy": "SKIP",
            "actions": ["Do not apply – domain mismatch too large"],
            "positioning": "Not suitable for this role",
            "cv_focus": [],
            "risk_mitigation": ["Avoid non-transferable domains"]
        }

    # =========================================
    # NORMAL FLOW
    # =========================================

    if score >= 60:
        strategy = "APPLY"
    elif score >= 45:
        strategy = "CONSIDER"
    else:
        strategy = "SKIP"

    actions = []

    if strategy == "APPLY":
        actions.append("Tailor CV to job")

    if engagement_type == "PERMANENT":
        actions.append("Emphasize motivation and cultural fit")

    if engagement_type == "PART_TIME":
        actions.append("Highlight flexibility and motivation")

    if engagement_type == "FREELANCE":
        actions.append("Highlight immediate impact and delivery capability")

    return {
        "strategy": strategy,
        "actions": actions,
        "positioning": "Align profile to role expectations",
        "cv_focus": ["Relevant experience", "Stakeholder alignment"],
        "risk_mitigation": []
    }