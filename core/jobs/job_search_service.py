import os
import time
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

            adzuna_start = time.time()

            print("===================================")
            print("[ADZUNA REQUEST START]")
            print("===================================")

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

            adzuna_data = {}

            for attempt in range(2):

                try:

                    print(
                        f"[ADZUNA ATTEMPT] "
                        f"{attempt + 1}"
                    )

                    adzuna_response = requests.get(
                        adzuna_url,
                        params=adzuna_params,
                        timeout=20
                    )

                    print(
                        f"[ADZUNA STATUS] "
                        f"{adzuna_response.status_code}"
                    )

                    if adzuna_response.status_code != 200:

                        print(
                            "[ADZUNA NON-200 RESPONSE]"
                        )

                        print(
                            adzuna_response.text[:500]
                        )

                        continue

                    try:

                        adzuna_data = (
                            adzuna_response.json()
                        )

                        break

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

                except requests.Timeout:

                    print(
                        "[ADZUNA TIMEOUT]"
                    )

                except Exception as request_error:

                    print(
                        "[ADZUNA REQUEST ERROR]"
                    )

                    print(str(request_error))

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

            adzuna_duration = (
                time.time() - adzuna_start
            )

            print(
                f"[ADZUNA RESULTS] "
                f"{len(adzuna_data.get('results', []))}"
            )

            print(
                f"[ADZUNA DURATION] "
                f"{round(adzuna_duration, 2)}s"
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

            jooble_start = time.time()

            print("===================================")
            print("[JOOBLE REQUEST START]")
            print("===================================")

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

            jooble_data = {}

            for attempt in range(2):

                try:

                    print(
                        f"[JOOBLE ATTEMPT] "
                        f"{attempt + 1}"
                    )

                    jooble_response = requests.post(
                        jooble_url,
                        json=jooble_payload,
                        timeout=20
                    )

                    print(
                        f"[JOOBLE STATUS] "
                        f"{jooble_response.status_code}"
                    )

                    if jooble_response.status_code != 200:

                        print(
                            "[JOOBLE NON-200 RESPONSE]"
                        )

                        print(
                            jooble_response.text[:500]
                        )

                        continue

                    try:

                        jooble_data = (
                            jooble_response.json()
                        )

                        break

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

                except requests.Timeout:

                    print(
                        "[JOOBLE TIMEOUT]"
                    )

                except Exception as request_error:

                    print(
                        "[JOOBLE REQUEST ERROR]"
                    )

                    print(str(request_error))

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

            jooble_duration = (
                time.time() - jooble_start
            )

            print(
                f"[JOOBLE RESULTS] "
                f"{len(jooble_data.get('jobs', []))}"
            )

            print(
                f"[JOOBLE DURATION] "
                f"{round(jooble_duration, 2)}s"
            )

        except Exception as e:

            print("===================================")
            print("=== JOOBLE FETCH ERROR ===")
            print("===================================")

            print(str(e))