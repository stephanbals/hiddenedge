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

# analysis/job_signal_extractor.py

def extract_job_signals(job_text: str):

    text = job_text.lower()

    signals = {
        "domain": None,
        "tech": [],
        "focus": []
    }

    # DOMAIN
    if "insurance" in text:
        signals["domain"] = "insurance"
    elif "bank" in text:
        signals["domain"] = "banking"

    # TECH
    for k in ["sap", "azure", "aws", "dynamics", "power bi", "fabric"]:
        if k in text:
            signals["tech"].append(k.upper())

    # 🔥 STRONG FOCUS DETECTION
    if "product owner" in text:
        signals["focus"].append("product ownership")

    if "customer" in text:
        signals["focus"].append("customer experience")

    if "commercial" in text or "sales" in text:
        signals["focus"].append("commercial enablement")

    if "crm" in text or "dynamics" in text:
        signals["focus"].append("crm platforms")

    if "data" in text:
        signals["focus"].append("data-driven decision making")

    if "stakeholder" in text:
        signals["focus"].append("stakeholder alignment")

    return signals