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

import hashlib


def generate_hash(role, company, url):

    text = f"{role}_{company}_{url}".lower()

    return hashlib.md5(text.encode()).hexdigest()


def is_duplicate(cursor, role, company, url):

    job_hash = generate_hash(role, company, url)

    cursor.execute(
        "SELECT id FROM opportunities WHERE duplicate_hash=?",
        (job_hash,)
    )

    result = cursor.fetchone()

    if result:
        return True

    return False


def add_hash(cursor, role, company, url):

    job_hash = generate_hash(role, company, url)

    return job_hash