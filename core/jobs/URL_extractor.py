
# =========================================
# URL Job Description Extractor (SAFE MVP)
# =========================================

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_job_description(url):

    try:
        response = requests.get(url, headers=HEADERS, timeout=5)

        if response.status_code != 200:
            return None

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Remove script/style
        for tag in soup(["script", "style"]):
            tag.extract()

        text = soup.get_text(separator="\n")

        # Clean up
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Heuristic: keep only meaningful content
        content = "\n".join(lines)

        # Basic sanity check
        if len(content) < 500:
            return None

        return content

    except Exception as e:
        print("URL extraction failed:", e)
        return None