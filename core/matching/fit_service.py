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

import re
import random

class FitService:

    def extract_keywords(self, text):
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        return list(set(words))


    def calculate_fit(self, cv_text, job_text):

        cv_keywords = set(self.extract_keywords(cv_text))
        job_keywords = set(self.extract_keywords(job_text))

        if not job_keywords:
            return self._empty_result()

        overlap = cv_keywords.intersection(job_keywords)

        # BASE SCORE
        raw_score = (len(overlap) / len(job_keywords)) * 100

        # ADD VARIATION (important for MVP realism)
        variation = random.randint(-15, 15)
        score = max(0, min(100, int(raw_score + variation)))

        strengths = list(overlap)[:8]
        gaps = list(job_keywords - overlap)[:8]

        # NEW DECISION LOGIC (more contrast)
        if score >= 55:
            decision = "APPLY"
        elif score <= 35:
            decision = "SKIP"
        else:
            decision = "CONSIDER"

        return {
            "fit_score": score,
            "strengths": strengths,
            "gaps": gaps,
            "decision": decision
        }


    def _empty_result(self):
        return {
            "fit_score": 0,
            "strengths": [],
            "gaps": [],
            "decision": "SKIP"
        }