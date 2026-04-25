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
# AIJobHunter V4 - Win Engine v2
# Domain-aware probability
# =========================================

def evaluate_win_probability(fit, gaps, opportunity, strategy):

    fit_score = fit.get("fit_score", 0)
    severity = gaps.get("gap_severity", "LOW")
    domain_mismatch = gaps.get("domain_mismatch", "NONE")

    prob = fit_score

    if severity == "HIGH":
        prob -= 20
    elif severity == "MEDIUM":
        prob -= 10

    if domain_mismatch == "CRITICAL":
        prob -= 30

    prob = max(0, min(100, prob))

    confidence = "LOW"
    if prob >= 70:
        confidence = "HIGH"
    elif prob >= 50:
        confidence = "MEDIUM"

    return {
        "win_probability": prob,
        "confidence": confidence,
        "factors": [
            f"Fit: {fit_score}",
            f"Severity: {severity}",
            f"Domain: {domain_mismatch}"
        ]
    }