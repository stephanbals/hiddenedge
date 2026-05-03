# =========================================
# HiddenEdge Matching Engine v1
# =========================================

import re


# =========================================
# HELPERS
# =========================================

def tokenize(text):
    words = re.findall(r'\b\w+\b', text.lower())
    return set(words)


def extract_keywords(text):
    tokens = tokenize(text)

    # basic filtering
    stopwords = {
        "the", "and", "for", "with", "you", "your", "are",
        "this", "that", "from", "have", "will", "can", "our",
        "job", "role", "work", "team", "experience"
    }

    return {w for w in tokens if len(w) > 3 and w not in stopwords}


def detect_domain(text):
    text = text.lower()

    if any(k in text for k in ["transformation", "change", "digital"]):
        return "transformation"

    if any(k in text for k in ["infrastructure", "cloud", "network"]):
        return "infrastructure"

    return "general"


def detect_seniority(text):
    text = text.lower()

    if "senior" in text or "lead" in text:
        return "senior"

    if "junior" in text:
        return "junior"

    return "mid"


# =========================================
# SCORING
# =========================================

def keyword_score(cv_keywords, job_keywords):

    if not job_keywords:
        return 0

    overlap = cv_keywords.intersection(job_keywords)

    return len(overlap) / len(job_keywords)


def domain_score(cv_domain, job_domain):

    if cv_domain == job_domain:
        return 1

    if job_domain == "general":
        return 0.6

    return 0.3


def seniority_score(cv_seniority, job_seniority):

    if cv_seniority == job_seniority:
        return 1

    if job_seniority == "mid":
        return 0.7

    return 0.4


def compute_fit(cv_text, job):

    cv_keywords = extract_keywords(cv_text)
    job_keywords = extract_keywords(job.get("description", ""))

    cv_domain = detect_domain(cv_text)
    job_domain = detect_domain(job.get("description", ""))

    cv_seniority = detect_seniority(cv_text)
    job_seniority = detect_seniority(job.get("title", ""))

    kw = keyword_score(cv_keywords, job_keywords)
    dom = domain_score(cv_domain, job_domain)
    sen = seniority_score(cv_seniority, job_seniority)

    fit = (kw * 0.5) + (dom * 0.3) + (sen * 0.2)

    return int(fit * 100)


# =========================================
# EXPLANATION
# =========================================

def generate_explanation(cv_text, job):

    reasons = []
    gaps = []

    text = cv_text.lower()
    job_text = job.get("description", "").lower()

    # domain
    job_domain = detect_domain(job_text)
    if job_domain in text:
        reasons.append(f"Matches {job_domain} experience")
    else:
        gaps.append(f"Limited {job_domain} exposure")

    # seniority
    job_seniority = detect_seniority(job.get("title", ""))
    if job_seniority == "senior" and "senior" not in text:
        gaps.append("Seniority not clearly positioned")
    else:
        reasons.append("Seniority aligned")

    # keyword gap
    job_keywords = extract_keywords(job_text)
    cv_keywords = extract_keywords(text)

    missing = list(job_keywords - cv_keywords)[:3]

    if missing:
        gaps.append("Missing: " + ", ".join(missing[:3]))

    return reasons, gaps


# =========================================
# MAIN MATCH FUNCTION
# =========================================

def match_jobs(cv_text, jobs):

    results = []

    for job in jobs:

        score = compute_fit(cv_text, job)
        reasons, gaps = generate_explanation(cv_text, job)

        results.append({
            "id": job.get("id"),
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "url": job.get("url"),
            "fit_score": score,
            "reasons": reasons,
            "gaps": gaps
        })

    results.sort(key=lambda x: x["fit_score"], reverse=True)

    return results[:5]