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