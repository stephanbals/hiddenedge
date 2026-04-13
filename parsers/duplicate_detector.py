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