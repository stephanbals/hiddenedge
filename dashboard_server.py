print("=== NEW BACKEND VERSION LOADED ===")

from flask import Flask, request, jsonify, render_template, redirect
import os
import stripe

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
# ANALYZE (UPGRADED)
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
        job_description = data.get("job_description", "").lower()

        # =========================
        # SIGNAL EXTRACTION
        # =========================

        keywords_match = [
            "project", "program", "stakeholder", "delivery",
            "transformation", "governance", "agile", "portfolio"
        ]

        keywords_mismatch = [
            "python", "developer", "engineering", "coding",
            "data science", "machine learning"
        ]

        match_hits = sum(1 for k in keywords_match if k in job_description)
        mismatch_hits = sum(1 for k in keywords_mismatch if k in job_description)

        # =========================
        # SCORING
        # =========================

        base_score = min(len(job_description) // 40, 100)
        score = max(0, min(base_score + (match_hits * 5) - (mismatch_hits * 5), 100))

        if score >= 75:
            decision = "Strong Apply"
            risk = "Low"
        elif score >= 50:
            decision = "Consider"
            risk = "Medium"
        else:
            decision = "Reject"
            risk = "High"

        # =========================
        # DETAILED OUTPUT
        # =========================

        recruiter_view = f"""
SUMMARY:
The candidate shows alignment with key transformation and delivery-related competencies.

MATCH STRENGTHS:
- Alignment with core program/project management keywords: {match_hits} matches detected
- Evidence of structured delivery, governance, and stakeholder coordination capabilities

GAPS / RISKS:
- Presence of non-aligned technical requirements: {mismatch_hits} indicators detected
- Potential mismatch if role is heavily technical or engineering-focused

SCREENING VERDICT:
Profile is {'strongly aligned' if score >= 75 else 'partially aligned' if score >= 50 else 'misaligned'} 
with typical expectations for transformation/program roles.
"""

        hiring_manager_view = f"""
EXECUTIVE ASSESSMENT:

The candidate demonstrates a background consistent with leading complex initiatives, 
particularly in transformation, governance, and delivery oversight.

VALUE CONTRIBUTION:
- Likely strong in structuring programs, aligning stakeholders, and driving execution
- Can bring immediate value in ambiguous or multi-stakeholder environments

CONCERNS:
- Role-specific technical depth may not be sufficient depending on expectations
- Requires validation against actual responsibilities (strategic vs hands-on execution)

RECOMMENDATION:
Proceed with {'interview' if score >= 60 else 'caution' if score >= 40 else 'no-go'}.

RISK LEVEL: {risk}
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
            "recruiter_view": "System error during analysis",
            "hiring_manager_view": str(e)
        })


# =========================
# STRIPE CHECKOUT
# =========================

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": "HiddenEdge Unlock"
                    },
                    "unit_amount": 1900,
                },
                "quantity": 1,
            }],
            success_url=request.host_url + "success",
            cancel_url=request.host_url + "app"
        )

        return jsonify({"url": session.url})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)