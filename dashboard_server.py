from flask import Flask, request, jsonify, render_template
import os
import json
import traceback
from openai import OpenAI
from docx import Document
import pdfplumber
import stripe

app = Flask(__name__)

# =========================
# CONFIG
# =========================
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")


# =========================
# FILE TEXT EXTRACTION
# =========================
def extract_text_from_file(file):
    filename = file.filename.lower()

    if filename.endswith(".docx"):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

    elif filename.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    elif filename.endswith(".txt"):
        return file.read().decode("utf-8")

    else:
        return ""


# =========================
# SAFE PARSER
# =========================
def safe_parse_ai_output(text):
    try:
        start = text.find('{')
        end = text.rfind('}') + 1

        if start == -1 or end == -1:
            raise ValueError("No JSON found")

        json_str = text[start:end]
        parsed = json.loads(json_str)

        def ensure_list(v): return v if isinstance(v, list) else []
        def ensure_str(v): return v if isinstance(v, str) else ""
        def ensure_int(v): return v if isinstance(v, int) else 0

        parsed["fit_score"] = ensure_int(parsed.get("fit_score"))
        parsed["decision"] = ensure_str(parsed.get("decision"))
        parsed["match_summary"] = ensure_str(parsed.get("match_summary"))

        parsed["strengths"] = ensure_list(parsed.get("strengths"))
        parsed["key_gaps"] = ensure_list(parsed.get("key_gaps"))
        parsed["cv_improvements"] = ensure_list(parsed.get("cv_improvements"))

        roles = parsed.get("recommended_roles", {})
        if not isinstance(roles, dict):
            roles = {}

        parsed["recommended_roles"] = {
            "strong_fit": ensure_list(roles.get("strong_fit")),
            "good_fit": ensure_list(roles.get("good_fit")),
            "stretch": ensure_list(roles.get("stretch"))
        }

        parsed["recruiter_view"] = ensure_str(parsed.get("recruiter_view"))
        parsed["hiring_manager_view"] = ensure_str(parsed.get("hiring_manager_view"))

        return parsed

    except Exception as e:
        print("PARSER ERROR:", str(e))
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
            "recruiter_view": "",
            "hiring_manager_view": ""
        }


# =========================
# AI ANALYSIS
# =========================
def analyze_cv_job(cv_text, job_text):

    system_prompt = """
You are an expert recruiter.

Return ONLY JSON:

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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CV:\n{cv_text}\n\nJOB:\n{job_text}"}
        ]
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Empty OpenAI response")

    return safe_parse_ai_output(content.strip())


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/app")
def app_page():
    return render_template("app.html")


@app.route("/eula")
def eula():
    return render_template("eula.html")


@app.route("/email")
def email():
    return render_template("email.html")


@app.route("/success")
def success():
    return render_template("success.html")


@app.route("/create-checkout-session")
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1
            }],
            success_url=request.host_url + "success",
            cancel_url=request.host_url + "app"
        )

        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("cv_file")
        job_text = request.form.get("job_text", "")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        cv_text = extract_text_from_file(file)

        if not cv_text.strip():
            return jsonify({"error": "Unreadable CV"}), 400

        result = analyze_cv_job(cv_text, job_text)

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)