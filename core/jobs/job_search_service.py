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

        print("===================================")
        print(
            f"[JOB SEARCH REGION] {current_region}"
        )
        print("===================================")

        region_results = []

        # =========================================
        # ADZUNA
        # =========================================

        try:

            print("[ADZUNA REQUEST START]")

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
                params=adzuna_params,
                timeout=20
            )

            print(
                f"[ADZUNA STATUS] "
                f"{adzuna_response.status_code}"
            )

            try:

                adzuna_data = (
                    adzuna_response.json()
                )

            except Exception as parse_error:

                print("===================================")
                print("=== ADZUNA PARSE ERROR ===")
                print("===================================")

                print(
                    "[ERROR]",
                    str(parse_error)
                )

                print(
                    "[STATUS]",
                    adzuna_response.status_code
                )

                print(
                    "[TEXT]",
                    adzuna_response.text[:500]
                )

                adzuna_data = {}

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

            print(
                f"[ADZUNA RESULTS] "
                f"{len(adzuna_data.get('results', []))}"
            )

        except Exception as e:

            print("===================================")
            print("=== ADZUNA FETCH ERROR ===")
            print("===================================")

            print(str(e))

        # =========================================
        # JOOBLE
        # =========================================

        try:

            print("[JOOBLE REQUEST START]")

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
                json=jooble_payload,
                timeout=20
            )

            print(
                f"[JOOBLE STATUS] "
                f"{jooble_response.status_code}"
            )

            try:

                jooble_data = (
                    jooble_response.json()
                )

            except Exception as parse_error:

                print("===================================")
                print("=== JOOBLE PARSE ERROR ===")
                print("===================================")

                print(
                    "[ERROR]",
                    str(parse_error)
                )

                print(
                    "[STATUS]",
                    jooble_response.status_code
                )

                print(
                    "[TEXT]",
                    jooble_response.text[:500]
                )

                jooble_data = {}

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

            print(
                f"[JOOBLE RESULTS] "
                f"{len(jooble_data.get('jobs', []))}"
            )

        except Exception as e:

            print("===================================")
            print("=== JOOBLE FETCH ERROR ===")
            print("===================================")

            print(str(e))

        if len(region_results) > 0:

            print(
                f"[REGION SUCCESS] "
                f"{len(region_results)} jobs found"
            )

            all_results.extend(
                region_results
            )

            break

        else:

            print(
                f"[REGION EMPTY] {current_region}"
            )

    print("===================================")
    print(
        f"[TOTAL JOB RESULTS] "
        f"{len(all_results[:10])}"
    )
    print("===================================")

    return all_results[:10]