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