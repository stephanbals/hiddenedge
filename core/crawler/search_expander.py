# =========================================
# SEARCH EXPANDER — STABLE VERSION
# =========================================

def expand_search_terms(user_input):

    if not user_input:
        return [
            "project manager",
            "program manager",
            "product owner"
        ]

    base = user_input.lower().strip()

    # normalize
    cleaned = base.replace("it ", "").replace("senior ", "").strip()

    ROLE_MAP = {
        "project manager": [
            "project manager",
            "it project manager",
            "technical project manager",
            "digital project manager",
            "sap project manager"
        ],
        "program manager": [
            "program manager",
            "programme manager",
            "it program manager",
            "transformation program manager"
        ],
        "product owner": [
            "product owner",
            "technical product owner",
            "agile product owner"
        ],
        "product manager": [
            "product manager",
            "digital product manager"
        ],
        "business analyst": [
            "business analyst",
            "it business analyst",
            "functional analyst"
        ]
    }

    expansions = set()
    expansions.add(base)

    for key, values in ROLE_MAP.items():
        if key in base:
            expansions.update(values)

    if len(expansions) <= 1:
        expansions.update([
            cleaned,
            "project manager",
            "program manager",
            "product owner"
        ])

    return list(expansions)[:8]