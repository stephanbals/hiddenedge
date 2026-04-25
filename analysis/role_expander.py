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

PREFIXES = [

    "IT",
    "Business",
    "Digital",
    "Enterprise",
    "SAP",
    "Cloud",
    "Platform"

]


SENIORITY = [

    "Senior",
    "Lead",
    "Principal",
    "Head",
    "Chief"

]


WORD_REPLACEMENTS = {

    "program":[
        "project",
        "delivery"
    ],

    "manager":[
        "lead",
        "director"
    ],

    "product":[
        "platform"
    ]

}


def expand_roles(base_roles):

    expanded = set()

    for role in base_roles:

        role = role.lower()

        expanded.add(role)

        words = role.split()

        # word replacement expansion
        for i, w in enumerate(words):

            if w in WORD_REPLACEMENTS:

                for replacement in WORD_REPLACEMENTS[w]:

                    new_words = words.copy()
                    new_words[i] = replacement

                    expanded.add(" ".join(new_words))

        # prefix expansion
        for p in PREFIXES:

            expanded.add(f"{p} {role}")

        # seniority expansion
        for s in SENIORITY:

            expanded.add(f"{s} {role}")

    return list(expanded)