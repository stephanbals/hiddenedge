# =========================================
# FIT ENGINE — CLEAN + STABLE
# =========================================

def evaluate_fit(cv_text, job_text):

    if not cv_text or not job_text:
        return {"fit_score": 0}

    cv_words = set(cv_text.lower().split())
    job_words = set(job_text.lower().split())

    if not job_words:
        return {"fit_score": 0}

    overlap = cv_words.intersection(job_words)

    score = (len(overlap) / len(job_words)) * 100

    # BOOST to avoid overly low scores
    score = min(100, score * 2)

    return {
        "fit_score": round(score, 2)
    }