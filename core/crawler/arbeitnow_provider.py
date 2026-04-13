# =========================================
# ARBEITNOW PROVIDER
# =========================================

import requests


def fetch_jobs():

    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        res = requests.get(url, timeout=10)
        data = res.json()

        return data.get("data", [])

    except:
        return []