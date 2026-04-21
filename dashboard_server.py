from flask import Flask, render_template, request, jsonify, redirect
import os
import stripe

# ===== APP INIT =====
app = Flask(__name__, static_folder="static", template_folder="templates")

# ===== STRIPE CONFIG =====
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")

# ================= ROUTES =================

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/eula")
def eula():
    return render_template("eula.html")


@app.route("/email")
def email():
    return render_template("email.html")


@app.route("/app")
def app_page():
    return render_template("app.html")


# ================= ANALYZE (FIXED) =================

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        # Minimal working response (no AI yet, just to unblock flow)
        return jsonify({
            "nestor": {
                "decision": "Strong Match",
                "fit_score": 82
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= STRIPE =================

@app.route("/create-checkout-session")
def create_checkout_session():
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[{
                "price": STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            success_url="https://hiddenedge-live.onrender.com/app?paid=true",
            cancel_url="https://hiddenedge-live.onrender.com/app",
        )

        return redirect(session.url, code=303)

    except Exception as e:
        return f"Stripe error: {str(e)}", 500


# ================= NO CACHE =================

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)