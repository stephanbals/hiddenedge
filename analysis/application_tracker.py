import sqlite3

DB = "database/jobs.db"


def mark_applied(job_id):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE opportunities
    SET status = 'applied'
    WHERE id = ?
    """, (job_id,))

    conn.commit()
    conn.close()


def mark_not_interested(job_id, reason="No"):

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE opportunities
    SET status = 'rejected'
    WHERE id = ?
    """, (job_id,))

    conn.commit()
    conn.close()