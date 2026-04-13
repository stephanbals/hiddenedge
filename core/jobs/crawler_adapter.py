# =========================================
# HiddenEdge – CRAWLER ADAPTER v2 (TARGETED)
# =========================================

import requests


ARBEITNOW_API = "https://www.arbeitnow.com/api/job-board-api"


def fetch_arbeitnow_jobs(limit=100):

    try:
        response = requests.get(ARBEITNOW_API, timeout=10)
        data = response.json()
        return data.get("data", [])[:limit]

    except Exception as e:
        print("Crawler error:", e)
        return []


# =========================================
# FILTER BY SEARCH QUERIES
# =========================================

def filter_by_queries(raw_jobs, queries):

    filtered = []

    for job in raw_jobs:

        title = (job.get("title") or "").lower()
        description = (job.get("description") or "").lower()

        text = f"{title} {description}"

        if any(q.lower() in text for q in queries):
            filtered.append(job)

    return filtered


# =========================================
# MAIN ENTRY
# =========================================

def get_jobs(queries=None, limit=100):

    raw_jobs = fetch_arbeitnow_jobs(limit)

    if not queries:
        return raw_jobs

    targeted = filter_by_queries(raw_jobs, queries)

    return targeted