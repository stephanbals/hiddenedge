import requests
import sqlite3
from datetime import datetime
import hashlib

DB = r"C:\Projects\AIJobHunter\database\jobs.db"


# ---------------------------------------
# HASH (DEDUPLICATION)
# ---------------------------------------
def job_hash(job):
    key = (job["role"] + job["company"] + job["url"]).lower()
    return hashlib.md5(key.encode()).hexdigest()


# ---------------------------------------
# SAVE JOB
# ---------------------------------------
def save_job(cursor, j):

    h = job_hash(j)

    cursor.execute("SELECT id FROM opportunities WHERE duplicate_hash=?", (h,))
    if cursor.fetchone():
        return False

    cursor.execute("SELECT id FROM opportunities WHERE url=?", (j["url"],))
    if cursor.fetchone():
        return False

    cursor.execute("""
    INSERT INTO opportunities (
        role, company, url, location, status, source, description, date_found, duplicate_hash
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        j["role"],
        j["company"],
        j["url"],
        j["location"],
        "new",
        j["source"],
        j["description"],
        datetime.now().isoformat(),
        h
    ))

    return True


# ---------------------------------------
# FILTER (IMPORTANT)
# ---------------------------------------
def is_relevant(job):

    text = (job["role"] + " " + job["description"]).lower()

    # must contain relevant keywords
    if not any(k in text for k in [
        "project manager",
        "program manager",
        "transformation",
        "sap",
        "portfolio",
        "pmo",
        "delivery lead",
        "it manager"
    ]):
        return False

    # exclude junk
    if any(k in text for k in [
        "marketing",
        "seo",
        "content",
        "social media",
        "sales"
    ]):
        return False

    return True


# ---------------------------------------
# FETCH ARBEITNOW
# ---------------------------------------
def fetch_arbeitnow():

    print("\n🌍 Arbeitnow (EU Jobs API)")

    url = "https://www.arbeitnow.com/api/job-board-api"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
    except Exception as e:
        print("Error:", e)
        return []

    jobs = []

    for item in data.get("data", []):

        job = {
            "role": item.get("title"),
            "company": item.get("company_name"),
            "url": item.get("url"),
            "location": item.get("location"),
            "source": "arbeitnow",
            "description": (item.get("description") or "")[:1000]
        }

        if not job["url"]:
            continue

        if is_relevant(job):
            jobs.append(job)

    print("Relevant jobs:", len(jobs))
    return jobs


# ---------------------------------------
# MAIN
# ---------------------------------------
def run_all():

    print("\n🚀 ARBEITNOW PIPELINE")

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    jobs = fetch_arbeitnow()

    total_seen = len(jobs)
    total_new = 0

    for j in jobs:
        if save_job(cursor, j):
            total_new += 1

    conn.commit()
    conn.close()

    print("\n======================")
    print("TOTAL FILTERED:", total_seen)
    print("TOTAL NEW:", total_new)
    print("======================\n")


if __name__ == "__main__":
    run_all()