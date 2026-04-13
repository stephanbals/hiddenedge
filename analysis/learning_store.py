import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

os.makedirs(DATA_DIR, exist_ok=True)

FILE = os.path.join(DATA_DIR, "rejections.json")


def save_rejection(job, reason):

    record = {
        "timestamp": datetime.now().isoformat(),
        "role": job.get("role"),
        "company": job.get("company"),
        "location": job.get("location"),
        "reason": reason
    }

    data = []

    if os.path.exists(FILE):
        try:
            with open(FILE, "r") as f:
                data = json.load(f)
        except:
            data = []

    data.append(record)

    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)