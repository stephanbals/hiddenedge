# =========================================
# HiddenEdge Scoring Engine v2
# SB3PM Advisory & Services Ltd
# =========================================

import math


# =========================================
# KEYWORD EXTRACTION (BASIC V1)
# =========================================

def extract_keywords_from_text(text):
    if not text:
        return []

    words = text.lower().split()

    # very basic filtering (can improve later)
    return list(set([w.strip(".,()") for w in words if len(w) > 3]))


# =========================================
# NORMALIZATION HELPERS
# =========================================

def normalize_keywords(keywords):
    if not keywords:
        return set()
    return set([k.strip().lower() for k in keywords])


def semantic_boost(job_keywords, candidate_keywords):
    """
    Light semantic expansion (rule-based)
    """
    synonyms = {
        "program manager": ["delivery lead", "program lead"],
        "transformation": ["change", "transformation", "modernization"],
        "ai": ["ai", "machine learning", "automation"],
        "data": ["data", "analytics", "bi"]
    }

    score = 0

    for _, syns in synonyms.items():
        if any(k in job_keywords for k in syns) and any(c in candidate_keywords for c in syns):
            score += 1

    return score


# =========================================
# FIT SCORE
# =========================================

def compute_fit_score(job, candidate):

    job_keywords = normalize_keywords(job.get("keywords", []))
    candidate_keywords = normalize_keywords(candidate.get("keywords", []))

    overlap = len(job_keywords & candidate_keywords)
    semantic = semantic_boost(job_keywords, candidate_keywords)

    # Capability (0–40)
    capability = min((overlap * 6) + (semantic * 4), 40)

    # Experience (0–25)
    experience = min(10 + (overlap * 3), 25)

    # Seniority (0–20)
    job_sen = job.get("seniority", "mid")
    cand_sen = candidate.get("seniority", "mid")

    if job_sen == cand_sen:
        seniority = 20
    elif cand_sen == "senior":
        seniority = 15
    else:
        seniority = 10

    # Domain (0–15)
    domain_overlap = semantic
    domain = min(domain_overlap * 5, 15)

    total = capability + experience + seniority + domain

    return min(round(total, 1), 100)


# =========================================
# OPPORTUNITY SCORE
# =========================================

def compute_opportunity_score(job, fit_score):

    fit_component = (fit_score / 100) * 4

    rate = job.get("rate", 0) or 0
    rate_component = min(rate / 250, 2)

    applicants = job.get("applicants", 50)
    competition_component = max(0, 1.5 - (applicants / 120))

    effort_component = 1.0

    days_old = job.get("days_old", 7)
    timing_component = max(0, 1.5 - (days_old / 12))

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
    if job.get("description"):
        signals += 1

    return round((signals / 5) * 100, 0)


# =========================================
# EXPLANATION LAYER
# =========================================

def explain_fit(job, candidate):

    job_keywords = normalize_keywords(job.get("keywords", []))
    candidate_keywords = normalize_keywords(candidate.get("keywords", []))

    overlap = job_keywords & candidate_keywords
    missing = job_keywords - candidate_keywords

    explanation = {
        "matched_keywords": list(overlap)[:5],
        "missing_keywords": list(missing)[:5],
        "summary": ""
    }

    if len(overlap) >= 5:
        explanation["summary"] = "Strong alignment with key requirements"
    elif len(overlap) >= 2:
        explanation["summary"] = "Partial alignment, some gaps remain"
    else:
        explanation["summary"] = "Low alignment with job requirements"

    return explanation


# =========================================
# MAIN ENTRY POINT (USE THIS)
# =========================================

def score_job(job, candidate):

    fit = compute_fit_score(job, candidate)
    opportunity = compute_opportunity_score(job, fit)
    decision = categorize(opportunity)
    confidence = compute_confidence(job, candidate)
    explanation = explain_fit(job, candidate)

    return {
        "fit_score": fit,
        "opportunity_score": opportunity,
        "decision": decision,
        "confidence": confidence,
        "explanation": explanation
    }
    # =========================================
# CV IMPROVEMENT LAYER (V1)
# =========================================

def suggest_cv_improvements(job, candidate):

    job_keywords = normalize_keywords(job.get("keywords", []))
    candidate_keywords = normalize_keywords(candidate.get("keywords", []))

    missing = list(job_keywords - candidate_keywords)

    suggestions = []

    # Limit suggestions to top 5
    for kw in missing[:5]:
        suggestions.append({
            "keyword": kw,
            "action": f"Add experience or mention of '{kw}' in CV",
            "impact": estimate_impact(kw)
        })

    return suggestions


def estimate_impact(keyword):
    """
    Simple heuristic for now
    Later: tie into real scoring delta
    """
    high_value = ["program", "transformation", "ai", "data", "delivery"]

    if keyword in high_value:
        return "+5 to +10 fit score"
    else:
        return "+2 to +5 fit score"
    