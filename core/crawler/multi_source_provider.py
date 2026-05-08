
if __name__ == "__main__":
    print("HiddenEdge Engine v1.0 | SB3PM")

# =========================================
# HiddenEdge — MULTI SOURCE PROVIDER
# UPGRADE: Better volume + smarter filtering
# NO REGRESSIONS
# =========================================

from concurrent.futures import ThreadPoolExecutor

from core.crawler.adzuna_provider import fetch_jobs as adzuna_jobs
from core.crawler.indeed_provider import fetch_jobs as indeed_jobs
from core.crawler.remotive_provider import fetch_jobs as remotive_jobs
from core.crawler.remoteok_provider import fetch_jobs as remoteok_jobs

from core.jobs.crawler_adapter import fetch_jooble

from core.crawler.job_adapter import normalize_jobs
from core.crawler.search_expander import expand_search_terms
from core.crawler.location_filter import filter_eu_jobs


# =========================================
# PROVIDERS
# =========================================

def jooble_wrapper(term):
    try:
        return normalize_jobs(fetch_jooble(query=term, location="europe"))
    except Exception as e:
        print("Jooble error:", e)
        return []


def fetch_provider(provider, term):
    try:
        return normalize_jobs(provider(term))
    except Exception as e:
        print("Provider error:", e)
        return []


# =========================================
# MAIN
# =========================================

def fetch_all_jobs(user_input=None):

    search_terms = expand_search_terms(user_input)

    providers = [
        adzuna_jobs,
        indeed_jobs,
        remotive_jobs,
        remoteok_jobs,
        jooble_wrapper
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

    # =========================================
    # 🔥 EXPANDED ROLE FILTER (LESS STRICT)
    # =========================================

    role_keywords = [
        "manager", "owner", "analyst",
        "lead", "coordinator", "consultant",
        "delivery", "program", "portfolio"
    ]

    filtered = []

    for j in all_jobs:
        title = (j.get("role") or j.get("title") or "").lower()

        if user_input and user_input.lower() in title:
            filtered.append(j)
        elif any(x in title for x in role_keywords):
            filtered.append(j)

    print("AFTER ROLE FILTER:", len(filtered))

    # =========================================
    # 🔥 SOFT EU FILTER (KEEP REMOTE)
    # =========================================

    eu_jobs = []

    for j in filtered:
        loc = (j.get("location") or "").lower()

        # Keep if EU match OR remote OR unclear (soft filter)
        if any(x in loc for x in [
            "belgium", "netherlands", "france", "germany",
            "spain", "italy", "poland", "sweden", "denmark",
            "europe", "remote"
        ]) or loc == "":
            eu_jobs.append(j)

    print("AFTER EU FILTER:", len(eu_jobs))

    # =========================================
    # 🔥 IMPROVED DEDUP (LESS AGGRESSIVE)
    # =========================================

    seen = set()
    unique = []

    for j in eu_jobs:
        key = (
            j.get("title"),
            j.get("company"),
            j.get("url")
        )

        if key not in seen:
            seen.add(key)
            unique.append(j)

    print("FINAL:", len(unique))

    return unique