# =========================================
# HiddenEdge CV Service - McKinsey-grade ATS Engine V6
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
            return self._fallback_basic()

        return analysis


    # =========================================
    # 🔥 CORE LLM
    # =========================================
    def _safe_llm_full_analysis(self, cv_text, job_text):
        try:
            raw = self._llm_full_analysis(cv_text, job_text)
            return self._safe_json_parse(raw)
        except Exception as e:
            print("LLM ERROR:", e)
            return None


    def _llm_full_analysis(self, cv_text, job_text):

        prompt = f"""
You are a top-tier strategy consultant and senior hiring authority.

Simulate a REAL hiring pipeline:
ATS → Recruiter → Hiring Manager

Be extremely analytical, structured, and evidence-based.

--------------------------------------------------
STEP 1 — ATS (DEEP EVALUATION MODEL)
--------------------------------------------------

Analyze JOB:

- domain
- role
- seniority
- critical_requirements (5–7)
- optional_requirements

Analyze CV:

- years_of_experience
- roles
- achievements
- skills
- tools
- scale_of_projects (budget, team size, geography if possible)

--------------------------------------------------
MATCH EACH CRITICAL REQUIREMENT:

For each:
- requirement
- match (yes / partial / no)
- strength (strong / medium / weak)
- evidence (SPECIFIC proof from CV)
- gap (explicit missing element)
- impact (high / medium / low)

--------------------------------------------------
BUILD SCORING MODEL:

Evaluate:

- capability_fit (0–100)
- experience_fit (0–100)
- domain_fit (0–100)
- complexity_fit (0–100)
- execution_risk (low / medium / high)

FINAL ATS SCORE:
Weighted combination prioritizing critical requirements.

--------------------------------------------------
STEP 2 — RECRUITER
--------------------------------------------------

- screening_decision (pass / borderline / reject)
- reasoning (clear and structured)
- red_flags
- shortlist_probability (0–100)

--------------------------------------------------
STEP 3 — HIRING MANAGER
--------------------------------------------------

- execution_readiness
- impact_potential
- risks (explicit)
- final_decision

--------------------------------------------------
STEP 4 — QUESTIONS
--------------------------------------------------

Generate 3–5 HIGH VALUE questions:
- uncover missing experience
- test weak areas
- improve candidate positioning

--------------------------------------------------
RETURN STRICT JSON:
--------------------------------------------------

{{
 "fit_score": 0,

 "ats_analysis": {{
   "domain": "",
   "role": "",
   "seniority": "",
   "score": 0,
   "reasoning": "",

   "scoring": {{
     "capability_fit": 0,
     "experience_fit": 0,
     "domain_fit": 0,
     "complexity_fit": 0,
     "execution_risk": ""
   }},

   "matches": [
     {{
       "requirement": "",
       "match": "",
       "strength": "",
       "evidence": "",
       "gap": "",
       "impact": ""
     }}
   ]
 }},

 "recruiter_view": {{
   "screening_decision": "",
   "reasoning": "",
   "red_flags": [],
   "shortlist_probability": ""
 }},

 "hiring_manager_view": {{
   "execution_readiness": "",
   "impact_potential": "",
   "risks": [],
   "final_decision": ""
 }},

 "questions": []
}}

CV:
{cv_text}

JOB:
{job_text}
"""

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

        return res.choices[0].message.content


    # =========================================
    # SAFE JSON
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

        print("JSON FAILED:", text)
        return None


    # =========================================
    # FALLBACK
    # =========================================
    def _fallback_basic(self):
        return {
            "fit_score": 30,
            "ats_analysis": {
                "domain": "Unknown",
                "role": "Unknown",
                "seniority": "Unknown",
                "score": 30,
                "reasoning": "Fallback mode",
                "scoring": {},
                "matches": []
            },
            "recruiter_view": {},
            "hiring_manager_view": {},
            "questions": []
        }


    def _empty_response(self, msg):
        return {
            "fit_score": 0,
            "ats_analysis": {},
            "recruiter_view": {},
            "hiring_manager_view": {},
            "questions": []
        }