# =========================================
# HiddenEdge / SB3PM Advisory & Services Ltd
# Author: Stephan Bals
# © 2026 SB3PM Advisory & Services Ltd
#
# This code is proprietary and confidential.
# Unauthorized use, distribution, or replication is prohibited.
# =========================================

from openai import OpenAI
import json
import re

print("HiddenEdge Engine v1.0 | SB3PM")

client = OpenAI()


# =========================================
# SAFE JSON PARSER (CRITICAL FIX)
# =========================================

def safe_parse_json(raw_text):

    print("RAW AI OUTPUT:\n", raw_text)

    if not raw_text:
        return {}

    try:
        # Remove markdown wrappers
        cleaned = re.sub(r"```json", "", raw_text, flags=re.IGNORECASE)
        cleaned = re.sub(r"```", "", cleaned)

        cleaned = cleaned.strip()

        # Extract JSON block
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        parsed = json.loads(cleaned)

        return parsed

    except Exception as e:
        print("JSON PARSE ERROR:", str(e))
        return {}


# =========================================
# CV SERVICE
# =========================================

class CVService:

    # =====================================
    # ANALYZE CV
    # =====================================
    def analyze_cv(self, texts, job_text):

        cv_text = "\n".join(texts)

        prompt = f"""
You are an expert recruiter and hiring manager.

STRICT RULES:
- Return ONLY valid JSON
- NO markdown
- NO ``` blocks
- If job description is too vague → clearly say so in match_summary

Return EXACT structure:

{{
  "fit_score": number,
  "decision": "",
  "advice": "",
  "match_summary": "",
  "strengths": [],
  "key_gaps": [],
  "cv_improvements": [],
  "learning_recommendations": [],
  "recruiter_view": "",
  "hiring_manager_view": "",
  "recommended_roles": {{
    "strong_fit": [],
    "good_fit": [],
    "stretch": []
  }}
}}

CV:
{cv_text}

JOB:
{job_text}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            raw_output = response.choices[0].message.content

            parsed = safe_parse_json(raw_output)

            # Ensure safe structure for UI
            return {
                "fit_score": parsed.get("fit_score"),
                "match_summary": parsed.get("match_summary"),
                "recruiter_view": parsed.get("recruiter_view"),
                "hiring_manager_view": parsed.get("hiring_manager_view"),
                "strengths": parsed.get("strengths", []),
                "key_gaps": parsed.get("key_gaps", []),
                "recommended_roles": parsed.get("recommended_roles", {}),
            }

        except Exception as e:
            print("ANALYZE ERROR:", str(e))

            return {
                "fit_score": None,
                "match_summary": "Error during analysis",
                "recruiter_view": "",
                "hiring_manager_view": "",
                "strengths": [],
                "key_gaps": [],
                "recommended_roles": {}
            }


    # =====================================
    # REFINE CV (TAILORING)
    # =====================================
    def refine_cv_with_answers(self, texts, job_text, answers):

        cv_text = "\n".join(texts)

        prompt = f"""
You are an expert CV writer.

Rewrite the CV into a clean, professional, structured format.

STRICT RULES:
- Return ONLY valid JSON
- NO markdown
- NO ``` blocks

Structure:

{{
  "name": "",
  "summary": "",
  "skills": [],
  "experience": [
    {{
      "company": "",
      "title": "",
      "duration": "",
      "bullets": []
    }}
  ]
}}

CV:
{cv_text}

JOB:
{job_text}

ANSWERS:
{answers}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            raw_output = response.choices[0].message.content

            parsed = safe_parse_json(raw_output)

            return {"cv": parsed}

        except Exception as e:
            print("REFINE ERROR:", str(e))
            return {"cv": {}}