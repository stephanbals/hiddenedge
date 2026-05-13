import os
import requests


# =========================================
# JOB SOURCE
# =========================================

def search_jobs_real_sources(
    keywords,
    region
):

    all_results = []

    fallback_regions = [
        region,
        "Netherlands",
        "Germany",
        "Remote",
        "Europe"
    ]

    seen = set()

    search_regions = []

    for r in fallback_regions:

        if r and r.lower() not in seen:

            search_regions.append(r)

            seen.add(r.lower())

    for current_region in search_regions:

        region_results = []

        # =========================================
        # ADZUNA
        # =========================================

        try:

            adzuna_url = (
                "https://api.adzuna.com/"
                "v1/api/jobs/be/search/1"
            )

            adzuna_params = {

                "app_id":
                    os.getenv(
                        "ADZUNA_APP_ID"
                    ),

                "app_key":
                    os.getenv(
                        "ADZUNA_APP_KEY"
                    ),

                "what":
                    keywords,

                "where":
                    current_region,

                "results_per_page":
                    5
            }

            adzuna_response = requests.get(
                adzuna_url,
                params=adzuna_params
            )

            adzuna_data = (
                adzuna_response.json()
            )

            for job in adzuna_data.get(
                "results",
                []
            ):

                region_results.append({

                    "id":
                        f"adzuna_{job.get('id')}",

                    "title":
                        job.get("title"),

                    "company":
                        job.get(
                            "company",
                            {}
                        ).get(
                            "display_name"
                        ),

                    "location":
                        job.get(
                            "location",
                            {}
                        ).get(
                            "display_name"
                        ),

                    "url":
                        job.get(
                            "redirect_url"
                        ),

                    "rate":
                        job.get(
                            "salary_max"
                        )
                })

        except Exception as e:

            print(
                "ADZUNA FETCH ERROR:",
                e
            )

        # =========================================
        # JOOBLE
        # =========================================

        try:

            jooble_key = os.getenv(
                "JOOBLE_API_KEY"
            )

            jooble_url = (
                f"https://jooble.org/api/"
                f"{jooble_key}"
            )

            jooble_payload = {

                "keywords":
                    keywords,

                "location":
                    current_region
            }

            jooble_response = requests.post(
                jooble_url,
                json=jooble_payload
            )

            jooble_data = (
                jooble_response.json()
            )

            for job in jooble_data.get(
                "jobs",
                []
            ):

                region_results.append({

                    "id":
                        f"jooble_{job.get('id')}",

                    "title":
                        job.get("title"),

                    "company":
                        job.get("company"),

                    "location":
                        job.get("location"),

                    "url":
                        job.get("link"),

                    "rate":
                        None
                })

        except Exception as e:

            print(
                "JOOBLE FETCH ERROR:",
                e
            )

        if len(region_results) > 0:

            all_results.extend(
                region_results
            )

            break

    return all_results[:10]