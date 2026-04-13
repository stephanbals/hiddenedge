# =========================================
# ADZUNA PROVIDER — STABLE VERSION
# =========================================

import requests

APP_ID = "demo"
APP_KEY = "demo"

EU_COUNTRIES = [
    "gb", "be", "nl", "fr", "de", "es",
    "it", "pt", "pl", "se", "no", "dk",
    "fi", "at", "ie"
]

PAGES = 3
RESULTS_PER_PAGE = 20


def fetch_jobs(search_term="project manager"):

    all_results = []

    for country in EU_COUNTRIES:

        for page in range(1, PAGES + 1):

            try:
                url = (
                    f"https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
                    f"?app_id={APP_ID}&app_key={APP_KEY}"
                    f"&results_per_page={RESULTS_PER_PAGE}"
                    f"&what={search_term}"
                    f"&content-type=application/json"
                )

                res = requests.get(url, timeout=10)

                if res.status_code != 200:
                    continue

                data = res.json()

                results = data.get("results", [])

                if not results:
                    break

                all_results.extend(results)

            except Exception as e:
                print("Adzuna error:", e)
                continue

    return all_results