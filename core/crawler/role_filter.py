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
# ROLE FILTER — TITLE-FIRST STRICT FILTER
# =========================================

TARGET_TITLES = [
    "project manager",
    "program manager",
    "programme manager",
    "delivery manager",
    "product owner",
    "product manager",
    "business analyst",
    "scrum master",
    "agile coach",
    "transformation",
    "sap",
    "data",
    "ai"
]

EXCLUDE_TITLES = [
    "intern",
    "praktikum",
    "trainee",
    "assistant",
    "support",
    "junior",
    "student",
    "working student",
    "customer support",
    "kundenservice"
]


def is_valid_job(job, user_input=None):

    title = (job.get("role") or "").lower()

    # ❌ HARD EXCLUDE BASED ON TITLE
    for bad in EXCLUDE_TITLES:
        if bad in title:
            return False

    # ✅ PRIMARY MATCH: TITLE ONLY
    if any(t in title for t in TARGET_TITLES):
        return True

    # ✅ USER INPUT BOOST
    if user_input:
        if user_input.lower() in title:
            return True

    return False


def filter_jobs(jobs, user_input=None):

    return [j for j in jobs if is_valid_job(j, user_input)]