# =========================================
# HiddenEdge CV Service — STABLE + FULL VERSION
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
    # ANALYZE CV (MAIN ENGINE)
    # =========================================
    def analyze_cv(self, texts, job_text):

        if not texts:
            return self._safe_default("No CV content provided.")

        if not job_text or len(job_text.strip()) < 20:
            return self._safe_default("Job description too short.")

        cv_text = "\n".join(texts)

        if not AI_ENABLED:
            return self._safe_default("AI not available.")

        try:
            raw = self._llm_analysis(cv_text, job_text)
            parsed = self._safe_json_parse(raw)

            if not parsed:
                return self._safe_default("AI returned invalid JSON")

            return self._normalize(parsed)

        except Exception as e:
            print("ANALYSIS ERROR:", e)
            return self._safe_default("Analysis failed")

    # =========================================
    # LLM ANALYSIS CALL
    # =========================================
    def _llm_analysis(self, cv_text, job_text):

        prompt = f"""
You are a senior recruiter + hiring manager + ATS system.

Analyze this CV against the job.

Return STRICT JSON ONLY.

{{
 "fit_score": number,
 "ats_analysis": {{
   "score": number,
   "domain": "string",
   "role": "string",
   "seniority": "string",
   "reasoning": "string",
   "matches": [
     {{
       "requirement": "string",
       "match": "yes/partial/no",
       "strength": "strong/medium/weak",
       "evidence": "specific CV evidence",
       "gap": "gap explanation"
     }}
   ]
 }},
 "recruiter_view": {{
   "screening_decision": "pass/reject/borderline",
   "reasoning": "string",
   "red_flags": ["string"],
   "shortlist_probability": "number%"
 }},
 "hiring_manager_view": {{
   "execution_readiness": "low/medium/high",
   "impact_potential": "low/medium/high",
   "risks": ["string"],
   "final_decision": "string"
 }},
 "questions": ["string"]
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
    # SAFE JSON PARSE
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
    # NORMALIZE OUTPUT (CRITICAL FIX)
    # =========================================
    def _normalize(self, data):

        return {
            "fit_score": data.get("fit_score", 60),

            "ats_analysis": {
                "score": data.get("ats_analysis", {}).get("score", 60),
                "domain": data.get("ats_analysis", {}).get("domain", "Unknown"),
                "role": data.get("ats_analysis", {}).get("role", "Unknown"),
                "seniority": data.get("ats_analysis", {}).get("seniority", "Unknown"),
                "reasoning": data.get("ats_analysis", {}).get("reasoning", ""),
                "matches": data.get("ats_analysis", {}).get("matches", [])
            },

            "recruiter_view": {
                "screening_decision": data.get("recruiter_view", {}).get("screening_decision", "borderline"),
                "reasoning": data.get("recruiter_view", {}).get("reasoning", ""),
                "red_flags": data.get("recruiter_view", {}).get("red_flags", []),
                "shortlist_probability": data.get("recruiter_view", {}).get("shortlist_probability", "N/A")
            },

            "hiring_manager_view": {
                "execution_readiness": data.get("hiring_manager_view", {}).get("execution_readiness", "N/A"),
                "impact_potential": data.get("hiring_manager_view", {}).get("impact_potential", "N/A"),
                "risks": data.get("hiring_manager_view", {}).get("risks", []),
                "final_decision": data.get("hiring_manager_view", {}).get("final_decision", "N/A")
            },

            "questions": data.get("questions", [])
        }

    # =========================================
    # SAFE DEFAULT (FALLBACK)
    # =========================================
    def _safe_default(self, msg):

        return {
            "fit_score": 50,

            "ats_analysis": {
                "score": 50,
                "domain": "Unknown",
                "role": "Unknown",
                "seniority": "Unknown",
                "reasoning": msg,
                "matches": []
            },

            "recruiter_view": {
                "screening_decision": "borderline",
                "reasoning": msg,
                "red_flags": [],
                "shortlist_probability": "N/A"
            },

            "hiring_manager_view": {
                "execution_readiness": "N/A",
                "impact_potential": "N/A",
                "risks": [],
                "final_decision": "N/A"
            },

            "questions": []
        }

    # =========================================
    # CV IMPROVEMENT (REAL — NOT REMOVED)
    # =========================================
    def refine_cv_with_answers(self, texts, job_text, answers):

        if not AI_ENABLED:
            return {
                "cv": "\n".join(texts),
                "fit_score": 60
            }

        cv_text = "\n".join(texts)

        prompt = f"""
Rewrite this CV into a high-end consulting CV (McKinsey-level).

Focus on:
- impact-driven bullet points
- quantified achievements
- strong action verbs
- alignment with job

CV:
{cv_text}

JOB:
{job_text}

EXTRA INFO:
{answers}

Return JSON:
{{
 "cv": "full rewritten CV",
 "fit_score": number
}}
"""

        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            parsed = self._safe_json_parse(res.choices[0].message.content)

            if not parsed:
                raise Exception("Invalid CV JSON")

            return parsed

        except Exception as e:
            print("CV IMPROVE ERROR:", e)

            return {
                "cv": cv_text,
                "fit_score": 65
            }