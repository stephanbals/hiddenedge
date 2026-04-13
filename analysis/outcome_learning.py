import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "database", "jobs.db")


def get_outcome_stats():

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role,
        COUNT(*) as total,
        SUM(CASE WHEN status IN ('Interview1','Interview2','Offer','Won') THEN 1 ELSE 0 END) as success,
        SUM(CASE WHEN status='NotFound' THEN 1 ELSE 0 END) as dead,
        SUM(CASE WHEN status='NotInterested' THEN 1 ELSE 0 END) as rejected
    FROM opportunities
    WHERE status IS NOT NULL
    GROUP BY role
    """)

    role_stats = cursor.fetchall()

    cursor.execute("""
    SELECT source,
        COUNT(*) as total,
        SUM(CASE WHEN status IN ('Interview1','Interview2','Offer','Won') THEN 1 ELSE 0 END) as success,
        SUM(CASE WHEN status='NotFound' THEN 1 ELSE 0 END) as dead,
        SUM(CASE WHEN status='NotInterested' THEN 1 ELSE 0 END) as rejected
    FROM opportunities
    WHERE status IS NOT NULL
    GROUP BY source
    """)

    source_stats = cursor.fetchall()

    conn.close()

    return role_stats, source_stats


def build_learning_model():

    role_stats, source_stats = get_outcome_stats()

    role_scores = {}
    source_scores = {}

    for role, total, success, dead, rejected in role_stats:

        success = success or 0
        dead = dead or 0
        rejected = rejected or 0

        if total > 0:
            score = (success / total) - (dead / total * 0.5) - (rejected / total * 0.8)
            role_scores[role] = score

    for source, total, success, dead, rejected in source_stats:

        success = success or 0
        dead = dead or 0
        rejected = rejected or 0

        if total > 0:
            score = (success / total) - (dead / total * 0.5) - (rejected / total * 0.8)
            source_scores[source] = score

    return role_scores, source_scores