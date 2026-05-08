# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# =========================================

from core.cv.cv_improver import improve_cv_with_answers
from core.cv.cv_repositioner import reposition_cv
from core.llm.llm_client import call_llm

import json


class CVService:

    # =========================================
    # SAFE JSON RECOVERY
    # =========================================

    def _safe_json_load(self, raw):

        try:
            return json.loads(raw)
        except:
            return None

    # =========================================
    # ENSURE STRUCTURE
    # =========================================

    def _normalize_response(self, data):

        if not isinstance(data, dict):
            data = {}

        ats = data.get("ats_analysis", {})
        recruiter = data.get("recruiter_view", {})
        manager = data.get("hiring_manager_view", {})

        return {
            "fit_score": data.get("fit_score", 35),

            "ats_analysis": {
                "summary": ats.get(
                    "summary",
                    "The CV could not be fully evaluated against the job requirements."
                ),
                "strengths": ats.get("strengths", []),
                "gaps": ats.get("gaps", []),
                "detailed_evaluation": ats.get(
                    "detailed_evaluation",
                    "Additional ATS-level evaluation could not be generated."
                )
            },

            "recruiter_view": {
                "reasoning": recruiter.get(
                    "reasoning",
                    "The profile requires further evaluation against the role expectations."
                ),
                "detailed_assessment": recruiter.get(
                    "detailed_assessment",
                    "A more detailed recruiter assessment could not be generated."
                )
            },

            "hiring_manager_view": {
                "decision_rationale": manager.get(
                    "decision_rationale",
                    "Additional assessment is required to determine alignment with the role."
                ),
                "detailed_assessment": manager.get(
                    "detailed_assessment",
                    "A more detailed hiring manager assessment could not be generated."
                )
            },

            "questions": data.get("questions", [
                "Can you provide more detail about your most relevant experience for this role?"
            ]),

            "suggested_roles": data.get("suggested_roles", []),

            "suggestion_reason": data.get(
                "suggestion_reason",
                "Additional adjacent roles may provide stronger alignment."
            )
        }

    # =========================================
    # ANALYZE CV
    # =========================================

    def analyze_cv(self, cv_texts, job_text):

        combined_cv = "\n".join(cv_texts)

        # =========================================
        # PRIMARY PROMPT
        # =========================================

        prompt = f"""
You are a senior recruiter, ATS evaluator, and hiring manager.

Evaluate the CV against the target role as if making a real hiring decision.

CRITICAL:
- Return ONLY valid JSON
- No markdown
- No explanations outside JSON
- ALWAYS include ALL required fields
- NEVER omit sections
- Be domain agnostic
- Adapt dynamically to industry and seniority
- ATS analysis, recruiter analysis, and hiring manager analysis MUST be detailed and substantial
- Each major analysis block should contain approximately 8–15 lines of meaningful professional evaluation
- Explain strengths, concerns, positioning, credibility, transferability, and hiring implications
- Avoid generic or superficial statements
- Provide realistic hiring reasoning similar to real enterprise recruitment discussions

Required JSON structure:

{{
  "fit_score": number,

  "ats_analysis": {{
    "summary": string,
    "strengths": [string],
    "gaps": [string],
    "detailed_evaluation": string
  }},

  "recruiter_view": {{
    "decision": string,
    "reasoning": string,
    "detailed_assessment": string
  }},

  "hiring_manager_view": {{
    "decision_rationale": string,
    "detailed_assessment": string
  }},

  "questions": [string],

  "suggested_roles": [string],

  "suggestion_reason": string
}}

CV:
{combined_cv}

JOB:
{job_text}
"""

        # =========================================
        # FIRST CALL
        # =========================================

        raw = call_llm(prompt)

        data = self._safe_json_load(raw)

        # =========================================
        # RECOVERY MODE
        # =========================================

        if not data:

            print("PRIMARY JSON FAILED — ENTERING RECOVERY MODE")

            compressed_cv = combined_cv[:4000]
            compressed_job = job_text[:2500]

            recovery_prompt = f"""
Return ONLY valid JSON.

NO markdown.
NO code fences.
NO explanations.

Keep answers concise but detailed.

ATS, recruiter, and hiring manager evaluations must still be substantial and meaningful.

Required structure:

{{
  "fit_score": number,

  "ats_analysis": {{
    "summary": string,
    "strengths": [string],
    "gaps": [string],
    "detailed_evaluation": string
  }},

  "recruiter_view": {{
    "reasoning": string,
    "detailed_assessment": string
  }},

  "hiring_manager_view": {{
    "decision_rationale": string,
    "detailed_assessment": string
  }},

  "questions": [string],

  "suggested_roles": [string],

  "suggestion_reason": string
}}

Analyze this CV against this role.

CV:
{compressed_cv}

JOB:
{compressed_job}
"""

            raw = call_llm(recovery_prompt)

            data = self._safe_json_load(raw)

        # =========================================
        # FINAL FAILURE
        # =========================================

        if not data:

            print("RECOVERY MODE FAILED")

            data = {}

        # =========================================
        # NORMALIZE STRUCTURE
        # =========================================

        data = self._normalize_response(data)

        ats = data["ats_analysis"]

        ats_reasoning = (
            ats["summary"] +
            "<br><br><b>Strengths:</b><br>" +
            "<br>".join(ats["strengths"]) +
            "<br><br><b>Gaps:</b><br>" +
            "<br>".join(ats["gaps"]) +
            "<br><br><b>Detailed ATS Evaluation:</b><br>" +
            ats["detailed_evaluation"]
        )

        recruiter_reasoning = (
            data["recruiter_view"]["reasoning"] +
            "<br><br>" +
            data["recruiter_view"]["detailed_assessment"]
        )

        hiring_manager_reasoning = (
            data["hiring_manager_view"]["decision_rationale"] +
            "<br><br>" +
            data["hiring_manager_view"]["detailed_assessment"]
        )

        return {
            "fit_score": data["fit_score"],

            "ats_analysis": {
                "reasoning": ats_reasoning
            },

            "recruiter_view": {
                "decision_rationale":
                    recruiter_reasoning
            },

            "hiring_manager_view": {
                "decision_rationale":
                    hiring_manager_reasoning
            },

            "questions": data["questions"],

            "role_suggestions":
                data["suggested_roles"],

            "suggestion_reason":
                data["suggestion_reason"]
        }

    # =========================================
    # REFINE CV
    # =========================================

    def refine_cv_with_answers(
        self,
        cv_texts,
        job_text,
        answers
    ):

        combined_cv = "\n".join(cv_texts)
        answers_text = "\n".join(answers)

        # =========================================
        # SMART REFINE LOGIC
        # =========================================

        if len(answers_text) > 200:

            improved_cv = reposition_cv(
                combined_cv,
                job_text,
                answers_text
            )

        else:

            improved_cv = improve_cv_with_answers(
                combined_cv,
                answers_text
            )

        return {
            "cv": improved_cv,
            "fit_score": 75
        }