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

# analysis/role_identity_extractor.py

def extract_role_identity(job_text: str):

    text = job_text.lower()

    identity = {
        "role_type": None,
        "seniority": None,
        "focus": [],
        "orientation": None
    }

    # ROLE TYPE
    if "product owner" in text:
        identity["role_type"] = "Product Owner"
    elif "program manager" in text:
        identity["role_type"] = "Program Manager"
    elif "project manager" in text:
        identity["role_type"] = "Project Manager"

    # SENIORITY
    if "senior" in text:
        identity["seniority"] = "senior"

    # FOCUS AREAS
    if "customer" in text:
        identity["focus"].append("customer experience")

    if "commercial" in text or "sales" in text:
        identity["focus"].append("commercial enablement")

    if "data" in text:
        identity["focus"].append("data-driven")

    if "crm" in text or "dynamics" in text:
        identity["focus"].append("crm")

    if "platform" in text or "digital" in text:
        identity["focus"].append("digital platforms")

    # ORIENTATION
    if "business" in text or "customer" in text:
        identity["orientation"] = "business-facing"
    else:
        identity["orientation"] = "delivery-focused"

    return identity