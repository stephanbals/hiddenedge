# =========================================
# HiddenEdge Outcome Learning Layer (MVP)
# SB3PM Advisory & Services Ltd
# =========================================

import json
import os
import time

DATA_FILE = "outcomes.json"


class OutcomeService:

    def __init__(self):
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump([], f)

    # =========================================
    # STORE APPLICATION
    # =========================================
    def track_application(self, data):

        record = {
            "job_title": data.get("job_title"),
            "company": data.get("company"),
            "fit_score": data.get("fit_score"),
            "answers": data.get("answers"),
            "result": "pending",
            "date": int(time.time())
        }

        db = self._load()
        db.append(record)
        self._save(db)

        return {"status": "saved"}


    # =========================================
    # UPDATE RESULT
    # =========================================
    def update_result(self, index, result):

        db = self._load()

        if 0 <= index < len(db):
            db[index]["result"] = result
            self._save(db)
            return {"status": "updated"}

        return {"error": "invalid index"}


    # =========================================
    # ANALYZE OUTCOMES
    # =========================================
    def analyze(self):

        db = self._load()

        if not db:
            return {"insights": ["No data yet."]}

        total = len(db)
        rejected = [x for x in db if x["result"] == "rejected"]
        interviews = [x for x in db if x["result"] == "interview"]

        insights = []

        # Score-based insight
        low_scores = [x for x in rejected if x["fit_score"] < 65]
        if len(low_scores) > 2:
            insights.append(
                "You are frequently rejected when your match score is below 65%."
            )

        # High-score success
        high_scores = [x for x in interviews if x["fit_score"] > 75]
        if len(high_scores) > 2:
            insights.append(
                "You are more successful when your match score exceeds 75%."
            )

        # Keyword insight (basic)
        if total > 3:
            insights.append(
                "Improve measurable achievements and keyword alignment to increase success rate."
            )

        return {
            "total_applications": total,
            "insights": insights
        }


    # =========================================
    # HELPERS
    # =========================================
    def _load(self):
        with open(DATA_FILE, "r") as f:
            return json.load(f)

    def _save(self, data):
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)