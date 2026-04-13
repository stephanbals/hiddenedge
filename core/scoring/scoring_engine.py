import math


# =========================================
# FIT SCORE
# =========================================

def compute_fit_score(job, candidate):

    job_keywords = set(job.get("keywords", []))
    candidate_keywords = set(candidate.get("keywords", []))

    overlap = len(job_keywords & candidate_keywords)

    # Capability (0–35)
    capability = min(overlap * 7, 35)

    # Experience relevance (0–25)
    if overlap >= 4:
        experience = 25
    elif overlap >= 2:
        experience = 18
    else:
        experience = 10

    # Seniority (0–20)
    job_sen = job.get("seniority", "mid")
    cand_sen = candidate.get("seniority", "mid")

    if job_sen == cand_sen:
        seniority = 20
    elif cand_sen == "senior":
        seniority = 15  # slight overqualification
    else:
        seniority = 10

    # Domain (0–20)
    if "data" in candidate_keywords and "data" in job_keywords:
        domain = 20
    elif "data" in job_keywords:
        domain = 10
    else:
        domain = 15

    total = capability + experience + seniority + domain

    return min(total, 100)


# =========================================
# OPPORTUNITY SCORE
# =========================================

def compute_opportunity_score(job, fit_score):

    # Normalize fit
    fit_component = (fit_score / 100) * 4

    # Rate
    rate = job.get("rate", 0) or 0
    rate_component = min(rate / 200, 2)  # scale

    # Competition proxy
    applicants = job.get("applicants", 50)
    competition_component = max(0, 1.5 - (applicants / 100))

    # Effort (default low)
    effort_component = 1.0

    # Timing
    days_old = job.get("days_old", 7)
    timing_component = max(0, 1.5 - (days_old / 10))

    score = (
        fit_component +
        rate_component +
        competition_component +
        effort_component +
        timing_component
    )

    return round(min(score, 10), 2)


# =========================================
# DECISION
# =========================================

def categorize(opportunity_score):

    if opportunity_score >= 7.5:
        return "APPLY"
    elif opportunity_score >= 5.5:
        return "MAYBE"
    else:
        return "IGNORE"


# =========================================
# CONFIDENCE
# =========================================

def compute_confidence(job, candidate):

    signals = 0

    if job.get("keywords"):
        signals += 1
    if candidate.get("keywords"):
        signals += 1
    if job.get("rate"):
        signals += 1
    if job.get("seniority"):
        signals += 1

    return round((signals / 4) * 100, 0)