def calculate_score(job):

    score = 0

    text = f"{job.get('role','')} {job.get('company','')} {job.get('location','')}".lower()


    # ---------------------------------------
    # ROLE MATCH (VERY IMPORTANT)
    # ---------------------------------------

    if "program manager" in text:
        score += 60

    if "project manager" in text:
        score += 50

    if "transformation" in text:
        score += 40

    if "sap" in text:
        score += 25


    # ---------------------------------------
    # FREELANCE PRIORITY (KEY CHANGE)
    # ---------------------------------------

    if any(x in text for x in ["freelance", "contract", "zzp", "interim"]):
        score += 40

    if any(x in text for x in ["6 months", "12 months", "day rate"]):
        score += 20


    # ---------------------------------------
    # LOCATION BOOST
    # ---------------------------------------

    if "belgium" in text:
        score += 25

    if "netherlands" in text:
        score += 20

    if "luxembourg" in text:
        score += 15

    if "remote" in text:
        score += 10


    # ---------------------------------------
    # PENALTIES (VERY IMPORTANT)
    # ---------------------------------------

    if any(x in text for x in [
        "junior",
        "intern",
        "support",
        "assistant",
        "customer service",
        "sales rep",
        "crypto trader"
    ]):
        score -= 50


    return score