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

from concurrent.futures import ThreadPoolExecutor

from core.crawler.adzuna_provider import fetch_jobs as adzuna_jobs
from core.crawler.indeed_provider import fetch_jobs as indeed_jobs
from core.crawler.remotive_provider import fetch_jobs as remotive_jobs
from core.crawler.remoteok_provider import fetch_jobs as remoteok_jobs

from core.crawler.job_adapter import normalize_jobs
from core.crawler.search_expander import expand_search_terms
from core.crawler.location_filter import filter_eu_jobs


def fetch_provider(provider, term):
    try:
        return normalize_jobs(provider(term))
    except:
        return []


def fetch_all_jobs(user_input=None):

    search_terms = expand_search_terms(user_input)

    providers = [
        adzuna_jobs,
        indeed_jobs,
        remotive_jobs,
        remoteok_jobs
    ]

    all_jobs = []

    print("SEARCH TERMS:", search_terms)

    with ThreadPoolExecutor(max_workers=8) as executor:

        futures = []

        for term in search_terms:
            for provider in providers:
                futures.append(executor.submit(fetch_provider, provider, term))

        for f in futures:
            all_jobs.extend(f.result())

    print("TOTAL RAW:", len(all_jobs))

    # LIGHT FILTER
    filtered = []

    for j in all_jobs:
        title = (j.get("role") or "").lower()

        if user_input and user_input.lower() in title:
            filtered.append(j)
        elif any(x in title for x in ["manager", "owner", "analyst"]):
            filtered.append(j)

    print("AFTER ROLE FILTER:", len(filtered))

    eu_jobs = filter_eu_jobs(filtered)

    print("AFTER EU FILTER:", len(eu_jobs))

    # DEDUP
    seen = set()
    unique = []

    for j in eu_jobs:
        key = (j.get("role"), j.get("company"))

        if key not in seen:
            seen.add(key)
            unique.append(j)

    print("FINAL:", len(unique))

    return unique