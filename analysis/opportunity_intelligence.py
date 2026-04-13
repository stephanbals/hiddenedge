import sqlite3
import os
from datetime import datetime, UTC

BASE_DIR = os.getcwd()

SIGNALS_DB = os.path.join(BASE_DIR,"database","signals.db")
JOBS_DB = os.path.join(BASE_DIR,"database","jobs.db")

print("")
print("AIJobHunter Opportunity Intelligence")
print("------------------------------------")

def load_signals():

    conn = sqlite3.connect(SIGNALS_DB)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT partner,client,program,score
    FROM signals
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def load_jobs():

    conn = sqlite3.connect(JOBS_DB)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role,company,url,date_found
    FROM opportunities
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


signals = load_signals()
jobs = load_jobs()

now = datetime.now(UTC)

for s in signals:

    partner = s[0]
    client = s[1]
    program = s[2]
    score = s[3]

    if score < 3:
        continue

    print("")
    print("Transformation Program Signal")
    print("-----------------------------")

    print("Partner:", partner)
    print("Client:", client)
    print("Program:", program)

    print("")
    print("Matching open roles")

    found = False

    for j in jobs:

        role = j[0]
        company = j[1]
        url = j[2]

        text = role.lower()

        if program in text or role in text:

            found = True

            print("")
            print("Role:", role)
            print("Recruiter:", company)

            print("Apply link:")
            print(url)

            print("Apply window:")
            print("Apply within next 7-10 days")

    if not found:
        print("No open roles detected yet for this program.")

print("")
print("Opportunity scan finished")
