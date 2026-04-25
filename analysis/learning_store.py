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