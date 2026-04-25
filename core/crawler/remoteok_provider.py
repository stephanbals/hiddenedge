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
# REMOTEOK PROVIDER (CLEAN - NO CIRCULAR IMPORTS)
# =========================================

import requests


def fetch_jobs(search_term="project manager"):

    try:
        url = "https://remoteok.com/api"
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return []

        data = res.json()

        # first element is metadata
        jobs = data[1:] if isinstance(data, list) else []

        results = []

        for job in jobs:

            title = (job.get("position") or "").lower()

            if not title:
                continue

            # match ANY word in search term
            words = search_term.lower().split()

            if any(w in title for w in words):
                results.append(job)

        return results

    except Exception as e:
        print("RemoteOK error:", e)
        return []