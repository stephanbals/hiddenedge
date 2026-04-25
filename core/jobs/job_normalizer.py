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
# HiddenEdge – JOB NORMALIZER v1
# =========================================

import re


# =========================================
# HELPERS
# =========================================

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.strip().split())


def normalize_location(location_raw):

    if not location_raw:
        return {"city": "", "country": ""}

    parts = [p.strip() for p in location_raw.split(",")]

    if len(parts) == 1:
        return {"city": parts[0], "country": ""}

    if len(parts) >= 2:
        return {
            "city": parts[0],
            "country": parts[-1]
        }

    return {"city": "", "country": ""}


def detect_seniority(text):

    text = text.lower()

    if any(x in text for x in ["director", "head", "lead", "principal"]):
        return "senior"

    if any(x in text for x in ["manager", "owner"]):
        return "mid"

    if any(x in text for x in ["analyst", "junior", "support"]):
        return "junior"

    return "unknown"


def detect_domain(text):

    text = text.lower()

    domains = [
        "insurance", "banking", "finance",
        "public", "government", "healthcare",
        "energy", "telecom"
    ]

    for d in domains:
        if d in text:
            return d

    return "unknown"


def extract_skills(text):

    text = text.lower()

    known_skills = [
        "sap", "data", "analytics", "cloud",
        "aws", "azure", "jira", "agile",
        "scrum", "python", "sql"
    ]

    skills = []

    for s in known_skills:
        if s in text:
            skills.append(s)

    return list(set(skills))


# =========================================
# MAIN NORMALIZER
# =========================================

def normalize_job(raw_job):

    role = clean_text(raw_job.get("title") or raw_job.get("role") or "")
    company = clean_text(raw_job.get("company") or "")
    location_raw = clean_text(raw_job.get("location") or "")
    description = clean_text(raw_job.get("description") or "")

    location = normalize_location(location_raw)

    full_text = f"{role} {description}"

    return {
        "role": role,
        "company": company,
        "location": location,
        "description": description,
        "skills": extract_skills(full_text),
        "domain": detect_domain(full_text),
        "seniority": detect_seniority(full_text)
    }


# =========================================
# DEDUPLICATION
# =========================================

def deduplicate_jobs(jobs):

    seen = set()
    unique = []

    for job in jobs:

        key = (
            job.get("role", "").lower(),
            job.get("company", "").lower()
        )

        if key in seen:
            continue

        seen.add(key)
        unique.append(job)

    return unique


# =========================================
# PIPELINE
# =========================================

def normalize_jobs(raw_jobs):

    normalized = []

    for job in raw_jobs:
        try:
            n = normalize_job(job)

            # minimal quality filter
            if not n["role"] or not n["description"]:
                continue

            normalized.append(n)

        except:
            continue

    # remove duplicates
    normalized = deduplicate_jobs(normalized)

    return normalized