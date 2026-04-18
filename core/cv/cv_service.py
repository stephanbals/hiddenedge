import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class CVService:

    # =========================================
    # 🧠 NESTOR — ANALYSIS (FREE)
    # =========================================
    def analyze_fit(self, texts, job_text):

        cv_text = "\n".join(texts)

        prompt = f"""
You are NESTOR, an expert career decision analyst.

Analyze the CV against the job description.

Return STRICT JSON ONLY:

{{
 "decision": "APPLY or SKIP",
 "fit_score": number (0-100),
 "heatmap": {{
   "skills":0-100,
   "experience":0-100,
   "tools":0-100,
   "domain":0-100,
   "seniority":0-100
 }},
 "summary": "...",
 "strengths": [],
 "gaps": [],
 "risk_flags": [],
 "improvement_hint": "short motivating sentence"
}}

RULES:
- Be realistic, not optimistic
- Identify real missing requirements
- If fit_score < 60 → likely SKIP
- No hallucination

CV:
{cv_text}

JOB:
{job_text}
"""

        try:
            r = client.chat.completions.create(
                model="gpt-5.3",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            content = r.choices[0].message.content.strip()

            # Ensure valid JSON
            return json.loads(content)

        except Exception as e:
            print("NESTOR ERROR:", e)

            return {
                "decision": "UNKNOWN",
                "fit_score": 50,
                "heatmap": {
                    "skills": 50,
                    "experience": 50,
                    "tools": 50,
                    "domain": 50,
                    "seniority": 50
                },
                "summary": "Fallback analysis",
                "strengths": ["Basic alignment"],
                "gaps": ["Missing detailed evaluation"],
                "risk_flags": ["Model fallback triggered"],
                "improvement_hint": "Try refining your CV."
            }

    # =========================================
    # 💳 ALEC — CV GENERATION (PAID)
    # =========================================
    def tailor_cv_to_job(self, texts, job_text):

        cv_text = "\n".join(texts)

        prompt = f"""
You are ALEC, an expert CV optimizer.

Rewrite the CV for the job description.

RULES:
- No hallucination
- Do NOT invent experience
- Improve clarity, structure, and alignment
- Use strong action language
- Make it ATS-friendly

OUTPUT:
Return clean CV text only (no explanations)

CV:
{cv_text}

JOB:
{job_text}
"""

        try:
            r = client.chat.completions.create(
                model="gpt-5.3",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )

            return {
                "cv": r.choices[0].message.content.strip()
            }

        except Exception as e:
            print("ALEC ERROR:", e)

            return {
                "cv": "Error generating CV. Please try again."
            }