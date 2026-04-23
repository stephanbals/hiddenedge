from flask import Flask, request, jsonify, render_template
import os
import json
from openai import OpenAI

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# =========================
# SAFE PARSER (STRICT)
# =========================
def safe_parse_ai_output(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON found")

        json_str = text[start:end]
        parsed = json.loads(json_str)

        # =========================
        # ENFORCE STRUCTURE
        # =========================

        def ensure_list(value):
            return value if isinstance(value, list) else []

        def ensure_string(value):
            return value if isinstance(value, str) else ""

        def ensure_int(value):
            return value if isinstance(value, int) else 0

        parsed["fit_score"] = ensure_int(parsed.get("fit_score", 0))
        parsed["decision"] = ensure_string(parsed.get("decision", ""))
        parsed["match_summary"] = ensure_string(parsed.get("match_summary", ""))

        parsed["strengths"] = ensure_list(parsed.get("strengths", []))
        parsed["key_gaps"] = ensure_list(parsed.get("key_gaps", []))
        parsed["cv_improvements"] = ensure_list(parsed.get("cv_improvements", []))

        # =========================
        # NESTED STRUCTURE FIX
        # =========================
        roles = parsed.get("recommended_roles", {})

        if not isinstance(roles, dict):
            roles = {}

        parsed["recommended_roles"] = {
            "strong_fit": ensure_list(roles.get("strong_fit", [])),
            "good_fit": ensure_list(roles.get("good_fit", [])),
            "stretch": ensure_list(roles.get("stretch", []))
        }

        parsed["recruiter_view"] = ensure_string(parsed.get("recruiter_view", ""))
        parsed["hiring_manager_view"] = ensure_string(parsed.get("hiring_manager_view", ""))

        return parsed

    except Exception:
        return {
            "fit_score": 0,
            "decision": "Error",
            "match_summary": "Parsing error occurred.",
            "strengths": [],
            "key_gaps": [],
            "cv_improvements": [],
            "recommended_roles": {
                "strong_fit": [],
                "good_fit": [],
                "stretch": []
            },
            "recruiter_view": "Unable to parse AI response.",
            "hiring_manager_view": "Unable to parse AI response."
        }


# =========================
# AI ANALYSIS
# =========================
def analyze_cv_job(cv_text, job_text):

    system_prompt = """
You are an expert recruiter and hiring manager evaluator.

You MUST return ONLY valid JSON. No explanations. No markdown. No code blocks.

STRICT RULES:
- Do NOT wrap JSON in ```
- Do NOT repeat JSON
- Do NOT include commentary
- All fields MUST be present

EVALUATION:

1. Fit score (0–100)
2. Decision: Apply | Consider | Reject

3. Match summary:
2–3 sentences explaining overall fit

4. Strengths:
3–5 bullet points

5. Key gaps:
3–5 bullet points

6. CV improvements:
3–5 actionable suggestions

7. Recommended roles:
Grouped into:
- strong_fit
- good_fit
- stretch
Each with role + reason

8. Recruiter view:
Short paragraph

9. Hiring manager view:
Short paragraph

RETURN EXACT JSON STRUCTURE:

{
  "fit_score": 0,
  "decision": "",
  "match_summary": "",
  "strengths": [],
  "key_gaps": [],
  "cv_improvements": [],
  "recommended_roles": {
    "strong_fit": [],
    "good_fit": [],
    "stretch": []
  },
  "recruiter_view": "",
  "hiring_manager_view": ""
}
"""

    user_prompt = f"""
CV:
{cv_text}

JOB DESCRIPTION:
{job_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    raw_output = response.choices[0].message.content.strip()

    parsed = safe_parse_ai_output(raw_output)

    return parsed


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("landing.html")


@app.route("/app")
def app_page():
    return render_template("app.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        cv_text = request.form.get("cv_text", "")
        job_text = request.form.get("job_text", "")

        result = analyze_cv_job(cv_text, job_text)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "fit_score": 0,
            "decision": "Error",
            "match_summary": str(e),
            "strengths": [],
            "key_gaps": [],
            "cv_improvements": [],
            "recommended_roles": {
                "strong_fit": [],
                "good_fit": [],
                "stretch": []
            },
            "recruiter_view": "Error occurred.",
            "hiring_manager_view": "Error occurred."
        })


# =========================
# RUN (RENDER SAFE)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)