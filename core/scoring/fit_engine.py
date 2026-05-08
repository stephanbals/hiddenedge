
# =========================================
# HiddenEdge — FIT ENGINE (STABLE, NO REGRESSION)
# - robust tokenization
# - light stabilization (no hardcoding)
# =========================================

import re


def _tokenize(text: str):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return set(tokens)


def evaluate_fit(cv_text, job_text):
    if not cv_text or not job_text:
        return {"fit_score": 0, "overlap": [], "missing": []}

    cv_tokens = _tokenize(cv_text)
    job_tokens = _tokenize(job_text)

    if not job_tokens:
        return {"fit_score": 0, "overlap": [], "missing": []}

    overlap = cv_tokens.intersection(job_tokens)
    missing = job_tokens.difference(cv_tokens)

    base_score = (len(overlap) / len(job_tokens)) * 100

    # --- light stabilization (non-destructive) ---
    if len(overlap) > 0 and base_score < 20:
        base_score = 20 + (base_score * 0.5)

    base_score = max(10, min(base_score, 90))

    return {
        "fit_score": round(base_score, 2),
        "overlap": list(overlap),
        "missing": list(missing)
    }