import sqlite3
import requests
import os
from bs4 import BeautifulSoup

BASE_DIR = os.getcwd()
DATABASE_PATH = os.path.join(BASE_DIR, "database", "jobs.db")

ROLE_KEYWORDS = {
    "program manager": 3,
    "programme manager": 3,
    "transformation manager": 3,
    "transformation lead": 3,
    "delivery manager": 3,
    "pmo manager": 3,
    "portfolio manager": 3,

    "agile coach": 2,
    "product owner": 2,
    "chief product owner": 2,
    "lead product owner": 2,
    "product manager": 2,

    "scrum master": 1,
    "release train engineer": 1
}

TRANSFORMATION_SIGNALS = [
    "sap s/4hana",
    "sap s4hana",
    "erp transformation",
    "digital transformation",
    "cloud migration",
    "platform modernization",
    "agile transformation",
    "enterprise transformation",
    "sap implementation"
]

LOCATION_KEYWORDS = [
    "belgium",
    "brussels",
    "netherlands",
    "amsterdam",
    "luxembourg",
    "germany",
    "remote"
]

print("AIJobHunter Intelligence Parser Starting")


def load_jobs():

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT company, title, url FROM jobs")

    rows = cursor.fetchall()

    conn.close()

    return rows


def fetch_text(url):

    try:

        response = requests.get(url, timeout=20)

        if response.status_code == 200:

            soup = BeautifulSoup(response.text, "html.parser")

            text = soup.get_text(separator=" ").lower()

            return text

    except:

        return None


def score_roles(text):

    score = 0

    for role, weight in ROLE_KEYWORDS.items():

        if role in text:

            score += weight

    return score


def detect_transformation(text):

    signals = []

    for s in TRANSFORMATION_SIGNALS:

        if s in text:

            signals.append(s)

    return signals


def keyword_score(text, keywords):

    score = 0

    for k in keywords:

        if k in text:

            score += 1

    return score


def parse_jobs():

    jobs = load_jobs()

    for job in jobs:

        company = job[0]
        title = job[1]
        url = job[2]

        print("")
        print("Analyzing:", title)

        text = fetch_text(url)

        if not text:
            continue

        role_score = score_roles(text)
        location_score = keyword_score(text, LOCATION_KEYWORDS)
        transformation = detect_transformation(text)

        print("Role score:", role_score)
        print("Location score:", location_score)

        if transformation:

            print("")
            print(">>> Transformation program signal detected <<<")
            print("Company:", company)
            print("Title:", title)
            print("Signals:", transformation)

        if role_score >= 3:

            print("")
            print(">>> High-value role detected <<<")
            print("Company:", company)
            print("Title:", title)
            print("URL:", url)


parse_jobs()

print("")
print("Parser finished")
