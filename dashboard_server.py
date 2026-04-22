print("=== NEW BACKEND VERSION LOADED ===")

from flask import Flask, request, jsonify, render_template
import os
import stripe
import re

app = Flask(__name__)

# =========================
# CONFIG
# =========================
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")

stripe.api_key = STRIPE_SECRET_KEY

FREE_LIMIT = 3
usage_counter = {}

# =========================
# UTIL: TEXT CLEANING
# =========================
def normalize(text):
    return re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())

# =========================
# UTIL: TOKEN EXTRACTION
# =========================
def extract_tokens(text):
    words = normalize(text).split()
    return set(words)

# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/app")
def app_page():
    return render_template("app.html", stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route("/eula")
def eula():
    return render_template("eula.html")

@app.route("/email")
def email():
    return render_template("email.html")

@app.route("/success")
def success():
    return render_template("success.html")

# =========================
# ANALYZE (CV vs JOB REAL COMPARISON)
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():
    user_id = request.remote_addr
    usage = usage_counter.get(user_id, 0)

    if usage >= FREE_LIMIT:
        return jsonify({"error": "PAYWALL"})

    usage_counter[user_id] = usage + 1

    try:
        data = request.json or {}

        job_description = data.get("job_description", "")
        cv_text = data.get("cv_text", "")

        if not cv_text:
            return jsonify({
                "fit_score": 0,
                "decision": "Error",
                "recruiter_view": "No CV provided",
                "hiring_manager_view": "Upload or provide CV text"
            })

        # =========================
        # TOKENIZATION
        # =========================
        job_tokens = extract_tokens(job_description)
        cv_tokens = extract_tokens(cv_text)

        # =========================
        # SIGNALS
        # =========================
        overlap = job_tokens.intersection(cv_tokens)
        overlap_score = len(overlap)

        job_unique = job_tokens - cv_tokens
        mismatch_score = len(job_unique)

        # =========================
        # DOMAIN DETECTION (DYNAMIC)
        # =========================
        technical_terms = {
            "python", "chemistry", "laboratory", "analysis",
            "chromatography", "engineering", "developer"
        }

        cv_technical = len(cv_tokens.intersection(technical_terms))
        job_technical = len(job_tokens.intersection(technical_terms))

        # =========================
        # SCORING
        # =========================
        score = int((overlap_score * 2) - (mismatch_score * 0.3))

        # domain mismatch penalty
        if job_technical > 5 and cv_technical < 2:
            score -= 40

        score = max(0, min(score, 100))

        if score >= 70:
            decision = "Strong Apply"
        elif score >= 40:
            decision = "Consider"
        else:
            decision = "Reject"

        # =========================
        # ROLE TARGETING (DYNAMIC)
        # =========================
        if score < 30:
            recommended_roles = ["Different domain required"]
        elif score < 60:
            recommended_roles = ["Adjacent roles", "Bridging positions"]
        else:
            recommended_roles = ["Direct match roles"]

        roles_text = "\n".join([f"- {r}" for r in recommended_roles])

        # =========================
        # OUTPUT
        # =========================
        recruiter_view = f"""
SUMMARY:
Overlap tokens: {overlap_score}
Mismatch tokens: {mismatch_score}

Key overlap examples:
{list(overlap)[:10]}

Screening verdict:
{"Aligned" if score >= 70 else "Partial" if score >= 40 else "Misaligned"}
"""

        hiring_manager_view = f"""
ASSESSMENT:
- Overlap strength: {overlap_score}
- Domain mismatch signals: {job_technical - cv_technical}

RECOMMENDATION:
{"Proceed" if score >= 60 else "Caution" if score >= 40 else "Reject"}

RECOMMENDED ROLES:
{roles_text}
"""

        return jsonify({
            "fit_score": score,
            "decision": decision,
            "recruiter_view": recruiter_view.strip(),
            "hiring_manager_view": hiring_manager_view.strip()
        })

    except Exception as e:
        return jsonify({
            "fit_score": 0,
            "decision": "Error",
            "recruiter_view": "System error",
            "hiring_manager_view": str(e)
        })


# =========================
# STRIPE
# =========================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": "HiddenEdge Unlock"},
                "unit_amount": 1900,
            },
            "quantity": 1,
        }],
        success_url=request.host_url + "success",
        cancel_url=request.host_url + "app"
    )

    return jsonify({"url": session.url})


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)