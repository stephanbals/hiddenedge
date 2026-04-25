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
import random
import time


# =========================================
# CONFIG
# =========================================

APP_ID = "5f4a1cc2"
APP_KEY = "05ee2cb197c619436f340126f1b411d6"

COUNTRIES = ["nl", "gb"]  # try NL first, fallback to GB


# =========================================
# MOCK FALLBACK
# =========================================

def generate_mock_jobs(count=30):
    titles = [
        "Senior IT Project Manager",
        "Program Manager",
        "Transformation Lead",
        "PMO Manager",
        "Portfolio Manager"
    ]

    companies = ["Accenture", "Deloitte", "Capgemini", "PwC"]

    locations = ["Brussels", "Amsterdam", "Remote"]

    jobs = []

    for i in range(count):
        jobs.append({
            "id": f"mock_{i}",
            "title": random.choice(titles),
            "company": random.choice(companies),
            "location": random.choice(locations),
            "description": "Mock job description",
            "url": "https://example.com"
        })

    return jobs


# =========================================
# FETCH FROM ADZUNA (WITH RETRY)
# =========================================

def fetch_from_adzuna(country):

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 30,
        "what": "project manager OR program manager OR transformation"
    }

    for attempt in range(3):  # 🔁 retry up to 3 times

        try:
            print(f"🔍 Attempt {attempt+1} - Adzuna ({country})")

            response = requests.get(url, params=params, timeout=8)

            print("STATUS:", response.status_code)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                print(f"📊 {len(results)} jobs from {country}")

                jobs = []

                for j in results:
                    jobs.append({
                        "id": j.get("id"),
                        "title": j.get("title"),
                        "company": (j.get("company") or {}).get("display_name", "Unknown"),
                        "location": (j.get("location") or {}).get("display_name", ""),
                        "description": (j.get("description") or "")[:1200],
                        "url": j.get("redirect_url") or ""
                    })

                if jobs:
                    return jobs

            else:
                print("❌ Error:", response.text[:200])

        except Exception as e:
            print("❌ Exception:", str(e))

        # wait before retry
        time.sleep(1)

    return []


# =========================================
# MAIN ENTRY
# =========================================

def get_jobs():

    for country in COUNTRIES:

        jobs = fetch_from_adzuna(country)

        if jobs:
            print(f"✅ Using ADZUNA ({country}) jobs: {len(jobs)}")
            return jobs

    print("⚠️ All sources failed → using MOCK jobs")

    return generate_mock_jobs(30)