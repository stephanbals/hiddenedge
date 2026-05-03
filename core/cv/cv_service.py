# =========================================
# HiddenEdge — CV SERVICE (SAFE PATCH v5)
# ADDED: DYNAMIC QUESTIONS + RICH REASONING
# NO REGRESSIONS
# =========================================

import os
import json
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a senior hiring panel: ATS + recruiter + hiring manager.

STRICT RULES:
- NO generic phrases
- NO repetition
- NO empty statements
- ONLY use evidence from CV
- If missing → "not evidenced"
- Transferable experience = "partial", NEVER "yes"
- "yes" ONLY if explicitly proven in CV

CRITICAL LOGIC:
- Some requirements are CRITICAL (domain, tools, mandatory experience)
- If a CRITICAL requirement is "no", candidate is NOT shortlisted / NOT selected

STYLE:
- Concrete
- Direct
- Insightful
- Real hiring language

RECRUITER:
- Think like a real recruiter screening CVs
- Evaluate domain, seniority, clarity, positioning
- Explain WHY candidate is / is not shortlisted

HIRING MANAGER:
- Think like delivery owner / exec
- Evaluate execution capability, scale, risk
- Provide clear decision with reasoning

QUESTIONS:
- Generate questions ONLY based on missing or weak evidence
- Questions must help strengthen CV
- Be specific to role + domain
- Max 5 questions

OUTPUT MUST:
- Reflect real hiring decisions
- Be internally consistent across ATS / recruiter / manager
"""

# =========================================
# HELPERS
# =========================================

def extract_json(text):
    try:
        return json.loads(text)
    except:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    return None


def validate(data):
    return isinstance(data, dict) and "ats_analysis" in data


def dedupe(lst):
    seen = set()
    out = []
    for x in lst or []:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out


# =========================================
# VALIDATION HELPERS
# =========================================

def has_placeholders(text):
    if not text:
        return True
    t = text.lower()
    return any(p in t for p in [
        "[your", "[year", "[company", "[job title"
    ])


def dropped_experience(original, generated):
    if not original or not generated:
        return True

    if len(generated) < 0.95 * len(original):
        return True

    return False


# =========================================
# CORE SERVICE
# =========================================

class CVService:

    def analyze_cv(self, cv_texts, job_text):

        cv = "\n\n".join(cv_texts)

        prompt = f"""
Return JSON:

{{
 "fit_score": number,

 "ats_analysis": {{
   "reasoning": "...",
   "matches":[
     {{
       "requirement":"",
       "match":"yes | partial | no",
       "evidence":"",
       "gap":"",
       "critical": true | false
     }}
   ]
 }},

 "recruiter_view": {{
   "screening_decision":"",
   "overall_impression":"",
   "strengths":[],
   "concerns":[],
   "decision_rationale":"",
   "shortlist_probability":""
 }},

 "hiring_manager_view": {{
   "final_decision":"",
   "execution_readiness":"",
   "impact_potential":"",
   "strengths":[],
   "risks":[],
   "decision_rationale":""
 }},

 "questions":[ "..."],

 "improvement_summary":""
}}

CV:
{cv}

JOB:
{job_text}
"""

        data = self._call(prompt)

        if not validate(data):
            data = self._fallback()

        # =========================================
        # HARD CONSTRAINT PROPAGATION (UNCHANGED)
        # =========================================

        ats = data.get("ats_analysis", {})
        matches = ats.get("matches", [])

        critical_fail = any(
            m.get("critical") and m.get("match") == "no"
            for m in matches
        )

        recruiter = data.get("recruiter_view", {})
        manager = data.get("hiring_manager_view", {})

        if critical_fail:
            recruiter["screening_decision"] = "Not shortlisted"
            recruiter["decision_rationale"] = "Critical domain or capability gap detected."

            manager["final_decision"] = "Not selected"
            manager["decision_rationale"] = "Candidate lacks mandatory domain/tool experience."

        # =========================================
        # SCORE NORMALIZATION
        # =========================================

        score = data.get("fit_score", 60)

        if critical_fail:
            score = min(score, 60)

        if score > 95:
            score = 95

        data["fit_score"] = score

        # CLEANUP
        recruiter["strengths"] = dedupe(recruiter.get("strengths"))
        recruiter["concerns"] = dedupe(recruiter.get("concerns"))

        manager["strengths"] = dedupe(manager.get("strengths"))
        manager["risks"] = dedupe(manager.get("risks"))

        # =========================================
        # 🔥 SAFE QUESTIONS (NO BREAK)
        # =========================================

        questions = data.get("questions")

        if not questions or not isinstance(questions, list):
            questions = [
                "Can you clarify your role in similar projects?",
                "Can you provide measurable impact from your work?",
                "Which tools or systems have you used in similar contexts?"
            ]

        data["questions"] = questions[:5]

        data["recruiter_view"] = recruiter
        data["hiring_manager_view"] = manager

        return data

    # =========================================
    # REFINE (UNCHANGED)
    # =========================================
    def refine_cv_with_answers(self, cv_texts, job_text, answers):

        cv = "\n\n".join(cv_texts)
        ans = "\n".join(answers)

        prompt = f"""
Improve CV WITHOUT losing any content.

RULES:
- DO NOT remove anything
- DO NOT shorten
- ONLY expand/improve
- Keep all roles and bullets

CV:
{cv}

JOB:
{job_text}

ANSWERS:
{ans}

Return JSON:
{{"cv":"...", "fit_score": number}}
"""

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": "Enhance CV without removing content."},
                {"role": "user", "content": prompt}
            ]
        )

        raw = res.choices[0].message.content
        parsed = extract_json(raw)

        if not parsed:
            parsed = {"cv": raw, "fit_score": 75}

        return parsed

    def _call(self, prompt):

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )

        raw = res.choices[0].message.content
        parsed = extract_json(raw)

        return parsed if parsed else {}

    def _fallback(self):
        return {
            "fit_score": 60,
            "ats_analysis": {"reasoning": "Fallback", "matches": []},
            "recruiter_view": {"screening_decision": "consider"},
            "hiring_manager_view": {"final_decision": "interview"},
            "questions": [],
            "improvement_summary": "Limited analysis."
        }