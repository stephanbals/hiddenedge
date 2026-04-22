print("=== NEW BACKEND VERSION LOADED ===")

from flask import Flask, request, jsonify, render_template, redirect
import os
import stripe

# FORCE correct template loading
app = Flask(__name__, template_folder="templates")

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
    try:
        return render_template("index.html")
    except Exception as e:
        return f"TEMPLATE ERROR (index.html): {str(e)}"


@app.route("/app")
def app_page():
    try:
        return render_template("app.html", stripe_public_key=STRIPE_PUBLIC_KEY)
    except Exception as e:
        return f"TEMPLATE ERROR (app.html): {str(e)}"


@app.route("/eula")
def eula():
    try:
        return render_template("eula.html")
    except Exception as e:
        return f"TEMPLATE ERROR (eula.html): {str(e)}"


@app.route("/email")
def email():
    try:
        return render_template("email.html")
    except Exception as e:
        return f"TEMPLATE ERROR (email.html): {str(e)}"


@app.route("/success")
def success():
    try:
        return render_template("success.html")
    except Exception as e:
        return f"TEMPLATE ERROR (success.html): {str(e)}"


# =========================
# ANALYZE
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
        # ROLE TARGETING
        # =========================

        if mismatch_hits > match_hits:
            recommended_roles = [
                "Technical Program Manager",
                "Data Program Manager",
                "IT Project Manager (Technical Environment)"
            ]
        elif match_hits >= 3:
            recommended_roles = [
                "Senior Program Manager",
                "Transformation Manager",
                "Portfolio Manager",
                "PMO Lead"
            ]
        else:
            recommended_roles = [
                "Project Manager",
                "PMO Analyst",
                "Delivery Coordinator"
            ]

        roles_text = "\n".join([f"- {role}" for role in recommended_roles])

        # =========================
        # OUTPUT
        # =========================

        recruiter_view = f"""
SUMMARY:
The candidate shows alignment with key transformation and delivery-related competencies.

MATCH STRENGTHS:
- Alignment with program/project keywords: {match_hits} matches
- Strong delivery and stakeholder coordination signals

GAPS:
- Non-aligned technical indicators: {mismatch_hits}

VERDICT:
{'Strong alignment' if score >= 75 else 'Partial alignment' if score >= 50 else 'Misaligned'}
"""

        hiring_manager_view = f"""
EXECUTIVE VIEW:

Strong background in structured delivery and transformation.

VALUE:
- Stakeholder alignment
- Program execution
- Governance

RISKS:
- Possible mismatch in technical depth depending on role

RECOMMENDATION:
{'Proceed to interview' if score >= 60 else 'Proceed with caution' if score >= 40 else 'Do not proceed'}

RISK LEVEL: {risk}

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