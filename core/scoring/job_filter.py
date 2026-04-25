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
# HiddenEdge – JOB FILTER v2 (RELAXED + SAFE)
# =========================================

import re


def normalize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def keyword_overlap(cv_text, job_text):

    cv_tokens = set(normalize(cv_text))
    job_tokens = set(normalize(job_text))

    return len(cv_tokens.intersection(job_tokens))


def is_relevant_job(master_cv, job):

    job_text = (job.get("role", "") + " " + job.get("description", "")).lower()
    cv_text = master_cv.lower()

    overlap = keyword_overlap(cv_text, job_text)

    # =========================================
    # RELAXED RULES
    # =========================================

    if overlap >= 8:
        return True

    if "manager" in job_text and overlap >= 5:
        return True

    if "pmo" in job_text or "program" in job_text:
        return True

    return False


def filter_jobs(master_cv, jobs):

    filtered = []

    for job in jobs:
        try:
            if is_relevant_job(master_cv, job):
                filtered.append(job)
        except:
            continue

    # 🔥 SAFETY: never return empty
    if len(filtered) == 0:
        return jobs[:20]

    return filtered