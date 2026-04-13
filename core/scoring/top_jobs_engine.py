# =========================================
# TOP JOBS ENGINE — CLEAN VERSION
# =========================================

from core.scoring.fit_engine import evaluate_fit
from core.scoring.gap_engine import evaluate_gaps
from core.scoring.opportunity_engine import evaluate_opportunity
from core.scoring.reasoning_engine import build_reasoning


def rank_jobs(master_cv, jobs, limit=5):

    ranked = []

    for job in jobs:

        job_text = (
            (job.get("role") or "") + " " +
            (job.get("description") or "")
        ).lower()

        fit = evaluate_fit(master_cv, job_text)
        gaps = evaluate_gaps(master_cv, job_text)
        opportunity = evaluate_opportunity(fit, gaps)

        decision = opportunity.get("decision", "IGNORE")

        reasoning = build_reasoning(fit, gaps, opportunity)

        ranked.append({
            "role": job.get("role"),
            "company": job.get("company"),
            "location": job.get("location"),
            "description": job.get("description"),
            "url": job.get("url"),
            "fit_score": fit.get("fit_score"),
            "opportunity_score": opportunity.get("score"),
            "decision": decision,
            "reasoning": reasoning
        })

    ranked = sorted(
        ranked,
        key=lambda x: x["opportunity_score"],
        reverse=True
    )

    return ranked[:limit]