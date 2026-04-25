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
# JOB ADAPTER — NORMALIZE + FIX ENCODING
# =========================================

def clean_text(text):

    if not text:
        return ""

    try:
        # fix common encoding issue (utf-8 misread)
        text = text.encode("latin1").decode("utf-8")
    except:
        pass

    # remove weird leftovers
    text = text.replace("\uFFFD", "")
    text = text.replace("â€™", "'")
    text = text.replace("â€“", "-")
    text = text.replace("â€œ", '"')
    text = text.replace("â€\x9d", '"')

    return text


def normalize_jobs(raw_jobs):

    normalized = []

    for job in raw_jobs:

        normalized.append({
            "role": clean_text(job.get("title") or job.get("position") or ""),
            "company": clean_text(
                job.get("company", {}).get("display_name")
                if isinstance(job.get("company"), dict)
                else job.get("company")
            ),
            "location": clean_text(
                job.get("location", {}).get("display_name")
                if isinstance(job.get("location"), dict)
                else job.get("location")
            ),
            "description": clean_text(
                job.get("description") or job.get("content") or ""
            ),
            "url": job.get("redirect_url") or job.get("url") or "#"
        })

    return normalized