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

from datetime import datetime


# ---------------------------------------
# US STATES LIST (CRITICAL FIX)
# ---------------------------------------

US_STATES = [
    "alabama","alaska","arizona","arkansas","california","colorado",
    "connecticut","delaware","florida","georgia","hawaii","idaho",
    "illinois","indiana","iowa","kansas","kentucky","louisiana",
    "maine","maryland","massachusetts","michigan","minnesota",
    "mississippi","missouri","montana","nebraska","nevada",
    "new hampshire","new jersey","new mexico","new york",
    "north carolina","north dakota","ohio","oklahoma","oregon",
    "pennsylvania","rhode island","south carolina","south dakota",
    "tennessee","texas","utah","vermont","virginia","washington",
    "west virginia","wisconsin","wyoming"
]


# ---------------------------------------
# FRESHNESS
# ---------------------------------------

def is_fresh(job, max_hours=72):

    try:
        if job.get("date_found"):
            dt = datetime.fromisoformat(job["date_found"])
            age = (datetime.now() - dt).total_seconds() / 3600
            return age <= max_hours
    except:
        pass

    return True


# ---------------------------------------
# GEO LOGIC (FIXED)
# ---------------------------------------

def is_usa_location(location):

    loc = location.lower()

    if "usa" in loc:
        return True

    for state in US_STATES:
        if state in loc:
            return True

    return False


def geo_adjustment(job):

    location = (job.get("location") or "").lower()

    # ---------------------------------------
    # HARD FILTER → USA ONSITE
    # ---------------------------------------

    if is_usa_location(location) and "remote" not in location:
        return -999

    # ---------------------------------------
    # PREFERRED REGIONS
    # ---------------------------------------

    if "belgium" in location:
        return 50

    if "netherlands" in location:
        return 40

    if "germany" in location:
        return 30

    if "luxembourg" in location:
        return 25

    # ---------------------------------------
    # REMOTE (fallback)
    # ---------------------------------------

    if "remote" in location:
        return 15

    # ---------------------------------------
    # UNKNOWN → penalize
    # ---------------------------------------

    if location == "":
        return -20

    # ---------------------------------------
    # OTHER COUNTRIES
    # ---------------------------------------

    return -10


# ---------------------------------------
# MAIN ENGINE
# ---------------------------------------

def get_top_opportunities(jobs, limit=5):

    candidates = []

    for j in jobs:

        status = j.get("status")

        if status not in [None, "", "New", "Applied"]:
            continue

        geo_adj = geo_adjustment(j)

        # HARD FILTER → REMOVE
        if geo_adj == -999:
            continue

        j["score"] += geo_adj

        if is_fresh(j):
            j["score"] += 10

        candidates.append(j)

    # SORT
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # REMOVE DUPLICATES
    seen = set()
    unique = []

    for j in candidates:
        key = (j.get("role") or "").lower()

        if key not in seen:
            seen.add(key)
            unique.append(j)

    # DIVERSITY
    final = []
    groups = {}

    for j in unique:

        role = (j.get("role") or "").lower()

        if "sap" in role:
            g = "sap"
        elif "program" in role:
            g = "program"
        elif "project" in role:
            g = "project"
        elif "scrum" in role:
            g = "scrum"
        else:
            g = "other"

        count = groups.get(g, 0)

        if count < 2:
            final.append(j)
            groups[g] = count + 1

        if len(final) >= limit:
            break

    return final