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

# analysis/enrichment_layer.py

from typing import List, Dict


def _to_int_year(val: str):
    try:
        return int(val[:4])
    except:
        return None


def detect_career_gaps(roles: List[Dict]) -> List[Dict]:
    gaps = []

    roles_sorted = sorted(
        roles,
        key=lambda x: _to_int_year(x.get("start", "")) or 0
    )

    for i in range(len(roles_sorted) - 1):
        current = roles_sorted[i]
        next_role = roles_sorted[i + 1]

        end_year = _to_int_year(current.get("end", ""))
        next_start_year = _to_int_year(next_role.get("start", ""))

        if end_year and next_start_year:
            if next_start_year - end_year > 1:
                gaps.append({
                    "from": end_year,
                    "to": next_start_year,
                    "type": "timeline_gap"
                })

    return gaps


def detect_weak_roles(roles: List[Dict]) -> List[Dict]:
    weak = []

    for r in roles:
        desc = r.get("description", [])

        if not desc or len(desc) < 2:
            weak.append({
                "company": r.get("company"),
                "issue": "low_information"
            })

    return weak


def generate_questions(roles: List[Dict]) -> List[str]:
    questions = []

    gaps = detect_career_gaps(roles)
    weak_roles = detect_weak_roles(roles)

    for g in gaps:
        questions.append(
            f"There appears to be a gap between {g['from']} and {g['to']}. What were you doing during this period?"
        )

    for r in weak_roles:
        questions.append(
            f"Can you provide more detail about your role at {r['company']} (scope, scale, responsibilities)?"
        )

    return questions