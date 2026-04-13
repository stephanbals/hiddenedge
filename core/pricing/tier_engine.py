# =========================================
# HiddenEdge – TIER ENGINE v1
# =========================================

TIERS = {
    "free": 3,
    "basic": 5,
    "pro": 10
}


def get_limit(plan: str) -> int:
    return TIERS.get(plan, 3)