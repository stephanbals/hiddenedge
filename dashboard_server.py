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


@app.route("/success")
def success():
    return redirect("/app?paid=true")


# ✅ GENERIC ROUTE FOR ALL STATIC PAGES (eula, email, etc.)
@app.route("/<page>")
def render_page(page):
    try:
        return render_template(f"{page}.html")
    except:
        return "Page not found", 404


# =========================
# ANALYZE (WORKING + PAYWALL)
# =========================

@app.route("/analyze", methods=["POST"])
def analyze():
    user_id = request.remote_addr

    usage = usage_counter.get(user_id, 0)

    if usage >= FREE_LIMIT:
        return jsonify({"error": "PAYWALL"})

    usage_counter[user_id] = usage + 1

    try:
        data = request.get_json(force=True)
        job_description = data.get("job_description", "")

        # Safe scoring logic
        score = min(len(job_description) // 50, 100)

        if score > 70:
            decision = "Strong Apply"
        elif score > 40:
            decision = "Consider"
        else:
            decision = "Reject"

        return jsonify({
            "fit_score": score,
            "decision": decision,
            "recruiter_view": "Candidate alignment based on provided job description.",
            "hiring_manager_view": "Profile shows partial alignment with role expectations."
        })

    except Exception as e:
        return jsonify({
            "fit_score": 0,
            "decision": "Error",
            "recruiter_view": "System error",
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
                    "unit_amount": 1900,  # €19
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