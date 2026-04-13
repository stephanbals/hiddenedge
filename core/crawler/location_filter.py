EU_ONLY = [
    "germany","france","belgium","netherlands","spain","italy",
    "poland","sweden","denmark","finland","norway","austria",
    "portugal","ireland","luxembourg","czech","hungary",
    "slovakia","slovenia","romania","bulgaria"
]


def is_eu(job):

    loc = (job.get("location") or "").lower()

    if "united states" in loc or "usa" in loc or "california" in loc:
        return False

    return any(country in loc for country in EU_ONLY) or "remote" in loc


def filter_eu_jobs(jobs):
    return [j for j in jobs if is_eu(j)]