import requests

def fetch_jobs(search_term="project manager"):

    try:
        url = f"https://remotive.com/api/remote-jobs?search={search_term}"
        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            return []

        data = res.json()

        return data.get("jobs", [])

    except:
        return []