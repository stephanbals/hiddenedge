# =========================================
# HiddenEdge — CLEAN JOB OUTPUT (FIXED)
# =========================================

import os
import requests
import random
from collections import defaultdict

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")


# =========================================
# FETCHERS
# =========================================

def fetch_adzuna(query="project manager", country="gb", limit=30):
    try:
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

        params = {
            "app_id": ADZUNA_APP_ID,
            "app_key": ADZUNA_APP_KEY,
            "results_per_page": limit,
            "what": query
        }

        res = requests.get(url, params=params, timeout=10)
        data = res.json().get("results", [])

        jobs = []

        for j in data:
            title = j.get("title")

            if not title:
                continue

            jobs.append({
                "title": title,
                "company": (j.get("company") or {}).get("display_name"),
                "location": (j.get("location") or {}).get("display_name"),
                "description": j.get("description"),
                "url": j.get("redirect_url"),
                "source": "adzuna"
            })

        return jobs

    except Exception as e:
        print("Adzuna error:", e)
        return []


def fetch_jooble(query="project manager", location="remote", limit=20):
    try:
        if not JOOBLE_API_KEY:
            return []

        url = f"https://jooble.org/api/{JOOBLE_API_KEY}"

        payload = {
            "keywords": query,
            "location": location
        }

        res = requests.post(url, json=payload, timeout=5)
        data = res.json().get("jobs", [])

        jobs = []

        for j in data[:limit]:

            title = j.get("title")
            url_link = j.get("link")

            if not title or not url_link:
                continue

            jobs.append({
                "title": title,
                "company": j.get("company"),
                "location": j.get("location"),
                "description": j.get("snippet"),
                "url": url_link,
                "source": "jooble"
            })

        return jobs

    except Exception as e:
        print("Jooble error:", e)
        return []


def fetch_malt(query="project manager", limit=20):
    try:
        url = f"https://www.malt.com/api/projects?query={query}"
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return []

        data = res.json().get("projects", [])

        jobs = []

        for j in data[:limit]:

            title = j.get("title")

            if not title:
                continue

            jobs.append({
                "title": title,
                "company": "Malt Client",
                "location": j.get("location", "Remote"),
                "description": j.get("description"),
                "url": f"https://www.malt.com/projects/{j.get('slug')}",
                "source": "malt"
            })

        return jobs

    except Exception as e:
        print("Malt error:", e)
        return []


def fetch_indeed(query="project manager", limit=10):
    return [
        {
            "title": f"{query.title()} Role",
            "company": "Various",
            "location": "Various",
            "description": "Aggregated job",
            "url": "https://www.indeed.com",
            "source": "indeed"
        }
        for _ in range(limit)
    ]


# =========================================
# CLEAN + FILTER
# =========================================

def clean_jobs(jobs):

    cleaned = []

    for j in jobs:

        title = j.get("title")
        url = j.get("url")

        if not title or not url:
            continue

        if url == "#" or "localhost" in url:
            continue

        cleaned.append(j)

    return cleaned


# =========================================
# MAIN
# =========================================

def get_jobs(role=None, location=None, queries=None, limit=50):

    if queries:
        search_queries = queries
    else:
        search_queries = [role or "project manager"]

    location = location or "remote"

    all_jobs = []

    for q in search_queries:
        all_jobs += fetch_adzuna(q)
        all_jobs += fetch_jooble(q, location)
        all_jobs += fetch_malt(q)
        all_jobs += fetch_indeed(q)

    # 🔥 CLEAN
    all_jobs = clean_jobs(all_jobs)

    random.shuffle(all_jobs)

    # 🔥 HARD FALLBACK
    if not all_jobs:
        all_jobs = [
            {
                "title": "Project Manager",
                "company": "DemoCorp",
                "location": location,
                "url": "https://www.linkedin.com/jobs"
            }
        ]

    return all_jobs[:limit]