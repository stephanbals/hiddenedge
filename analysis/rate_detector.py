import re


def detect_rate(text):

    if not text:
        return None, None

    text = text.lower()

    patterns = [

        r"€\s?(\d{3,4})\s?/?day",
        r"€\s?(\d{3,4})\s?per day",
        r"(\d{3,4})\s?€\s?/?day",
        r"(\d{3,4})\s?€/day",

        r"€\s?(\d{3,4})\s?-\s?€?(\d{3,4})\s?/?day",
        r"(\d{3,4})\s?-\s?(\d{3,4})\s?€/day",

        r"\$(\d{2,3})\s?/hour",
        r"\$(\d{2,3})\s?per hour"
    ]

    for p in patterns:

        m = re.search(p, text)

        if m:

            if len(m.groups()) == 1:

                rate = int(m.group(1))

                return rate, rate

            if len(m.groups()) == 2:

                r1 = int(m.group(1))
                r2 = int(m.group(2))

                return r1, r2

    return None, None