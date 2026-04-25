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
# INDEED PROVIDER — RSS BASED (HIGH VOLUME)
# =========================================

import requests
import xml.etree.ElementTree as ET


def fetch_jobs(search_term="project manager"):

    jobs = []

    try:
        url = f"https://rss.indeed.com/rss?q={search_term}&l=Europe"

        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return []

        root = ET.fromstring(res.content)

        for item in root.findall(".//item"):

            jobs.append({
                "title": item.findtext("title"),
                "company": item.findtext("author"),
                "location": "Europe",
                "description": item.findtext("description"),
                "url": item.findtext("link")
            })

    except Exception as e:
        print("Indeed error:", e)

    return jobs