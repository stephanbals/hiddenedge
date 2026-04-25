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

import requests

def fetch_jobs(search_term="project manager"):

    try:
        url = f"https://remotive.com/api/remote-jobs?search={search_term}"
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return []

        data = res.json()

        return data.get("jobs", [])

    except:
        return []