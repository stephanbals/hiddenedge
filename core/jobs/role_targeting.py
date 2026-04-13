# =========================================
# HiddenEdge – ROLE TARGETING v1
# =========================================

import re


# =========================================
# HELPERS
# =========================================

def normalize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


# =========================================
# ROLE EXTRACTION
# =========================================

ROLE_KEYWORDS = [
    "program manager",
    "project manager",
    "portfolio manager",
    "pmo",
    "transformation",
    "delivery",
    "governance"
]


def extract_role_targets(cv_text):

    cv_text = cv_text.lower()

    targets = []

    for role in ROLE_KEYWORDS:
        if role in cv_text:
            targets.append(role)

    # fallback if nothing found
    if not targets:
        targets = ["project manager"]

    return list(set(targets))


# =========================================
# SEARCH QUERY BUILDER
# =========================================

def build_search_queries(role_targets):

    queries = []

    for r in role_targets:

        if "program" in r:
            queries.append("Program Manager")

        if "project" in r:
            queries.append("Project Manager")

        if "portfolio" in r or "pmo" in r:
            queries.append("PMO Manager")
            queries.append("Portfolio Manager")

        if "transformation" in r:
            queries.append("Transformation Manager")

        if "governance" in r:
            queries.append("PMO Governance")

    # remove duplicates
    return list(set(queries))