# =========================================
# HiddenEdge CV Service - ATS + Recruiter + Manager Engine V7
# SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# =========================================

import os
import json
import re

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    AI_ENABLED = True
except:
    AI_ENABLED = False


class CVService:

    # =========================================
    # MAIN ENTRY
    # =========================================
    def analyze_cv(self, texts, job_text):

        if not texts:
            return self._empty_response("No CV content provided.")

        if not job_text or len(job_text.strip()) < 30:
            return self._empty_response("Job description too vague.")

        cv_text = "\n".join(texts)

        if not AI_ENABLED:
            return self._empty_response("AI not available.")

        analysis = self._safe_llm_full_analysis(cv_text, job_text)

        if not analysis:
            return self._fallback_basic(cv_text, job_text)

        return analysis


    # =========================================
    # SAFE FULL ANALYSIS
    # =========================================
    def _safe_llm_full_analysis(self, cv_text, job_text):
        try:
            raw = self._llm_full_analysis(cv_text, job_text)
            parsed = self._safe_json_parse(raw)

            if parsed:
                self._sanitize_analysis(parsed)

            return parsed

        except Exception as e:
            print("Full analysis error:", e)
            return None


    # =========================================
    # CORE LLM PROMPT (ATS + HUMAN PIPELINE)
    # =========================================
    def _llm_full_analysis(self, cv_text, job_text):

        prompt = f"""
You simulate a REAL hiring pipeline:
ATS → Recruiter → Hiring Manager

Be analytical, evidence-based, and concrete.

--------------------------------
STEP 1 — ATS ANALYSIS
--------------------------------

Extract JOB:
- domain
- role_title
- seniority
- critical_requirements (5–7)

Extract CV:
- experience
- skills
- roles

Build MATCH TABLE:

For each requirement:
- requirement
- match (yes / partial / no)
- strength (strong / medium / weak)
- evidence (MUST be concrete sentence or fact from CV)
- gap

Rules:
- NEVER output "undefined"
- If no evidence → say: "No direct evidence found in CV"

Also calculate:
- ats_score (0–100)
- reasoning

--------------------------------
STEP 2 — RECRUITER
--------------------------------

- screening_decision (pass / borderline / reject)
- reasoning
- red_flags
- shortlist_probability (0–100)

--------------------------------
STEP 3 — HIRING MANAGER
--------------------------------

- execution_readiness
- impact_potential
- risks
- final_decision

--------------------------------
STEP 4 — QUESTIONS
--------------------------------

Generate 3–5 targeted improvement questions.

--------------------------------
RETURN STRICT JSON
--------------------------------
"""

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt + "\n\nCV:\n" + cv_text + "\n\nJOB:\n" + job_text}],
            temperature=0.2
        )

        return res.choices[0].message.content


    # =========================================
    # SANITIZER (REMOVES "undefined")
    # =========================================
    def _sanitize_analysis(self, data):

        ats = data.get("ats_analysis", {})

        for m in ats.get("matches", []):
            if not m.get("evidence") or m["evidence"].lower() == "undefined":
                m["evidence"] = "No direct evidence found in CV"

            if not m.get("gap"):
                if m.get("match") == "yes":
                    m["gap"] = "No major gap identified"
                else:
                    m["gap"] = "Gap not clearly specified"

        return data


    # =========================================
    # CV IMPROVEMENT ENGINE (CONSULTING-GRADE)
    # =========================================
    def refine_cv_with_answers(self, texts, job_text, answers):

        if not texts:
            return {"cv": "", "fit_score": 0}

        cv_text = "\n".join(texts)

        if not AI_ENABLED:
            return {
                "cv": cv_text,
                "fit_score": 60
            }

        try:
            prompt = f"""
You are a top-tier management consulting CV expert (McKinsey / BCG level).

Your task:
Rewrite the CV into a HIGH-IMPACT, RESULTS-DRIVEN, EXECUTIVE-LEVEL document.

--------------------------------
INPUT CV:
{cv_text}

--------------------------------
JOB DESCRIPTION:
{job_text}

--------------------------------
USER INPUT:
{answers}

--------------------------------
RULES (STRICT):

1. ALL experience must be bullet-based
2. Each bullet:
   → Action verb + context + measurable impact

3. Use metrics where possible:
   € / % / scale / team size

4. Remove:
   - vague statements
   - fluff
   - repetition

5. Add:
   - job-relevant keywords (ATS optimization)
   - stronger positioning (but no fabrication)

--------------------------------
STRUCTURE (MANDATORY):

NAME / TITLE

SUMMARY
(3–4 lines, sharp positioning)

KEY SKILLS
- Bullet list aligned to job

PROFESSIONAL EXPERIENCE

Company — Role — Dates
• Bullet (impact-driven)
• Bullet
• Bullet

--------------------------------
STYLE:
- concise
- sharp
- executive
- no long paragraphs

--------------------------------
RETURN JSON ONLY:

{{
 "cv": "FULL REWRITTEN CV",
 "fit_score": 85
}}
"""

            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            parsed = self._safe_json_parse(res.choices[0].message.content)

            if not parsed:
                return {
                    "cv": cv_text,
                    "fit_score": 65
                }

            return parsed

        except Exception as e:
            print("CV improvement error:", e)

            return {
                "cv": cv_text,
                "fit_score": 60
            }


    # =========================================
    # SAFE JSON PARSER
    # =========================================
    def _safe_json_parse(self, text):

        try:
            return json.loads(text)
        except:
            try:
                match = re.search(r'\{.*\}', text, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except:
                pass

        print("JSON PARSE FAILED:", text)
        return None


    # =========================================
    # FALLBACK
    # =========================================
    def _fallback_basic(self, cv, job):

        return {
            "fit_score": 20,
            "match_summary": "Fallback analysis used.",
            "ats_analysis": {
                "domain": "Unknown",
                "role": "Unknown",
                "seniority": "Unknown",
                "score": 20,
                "reasoning": "AI fallback used.",
                "matches": []
            },
            "decision": {
                "action": "Unknown",
                "reasoning": "AI processing failed."
            },
            "recruiter_view": {
                "screening_decision": "Unknown",
                "reasoning": "",
                "red_flags": [],
                "shortlist_probability": "Low"
            },
            "hiring_manager_view": {
                "execution_readiness": "",
                "impact_potential": "",
                "risks": [],
                "final_decision": ""
            },
            "questions": []
        }


    # =========================================
    # EMPTY
    # =========================================
    def _empty_response(self, msg):
        return {
            "fit_score": 0,
            "match_summary": msg,
            "ats_analysis": {},
            "decision": {},
            "recruiter_view": {},
            "hiring_manager_view": {},
            "questions": []
        }