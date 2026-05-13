from flask import Blueprint, render_template

page_routes = Blueprint(
    "page_routes",
    __name__
)

# =========================================
# PAGE ROUTES
# =========================================

@page_routes.route("/")
def index():
    return render_template("index.html")


@page_routes.route("/eula")
def eula():
    return render_template("eula.html")


@page_routes.route("/privacy")
def privacy():
    return render_template("privacy.html")


@page_routes.route("/email")
def email():
    return render_template("email.html")


@page_routes.route("/app")
def app_page():
    return render_template("app.html")


@page_routes.route("/payment")
def payment():
    return render_template("payment.html")


@page_routes.route("/payment-cancel")
def payment_cancel():
    return render_template(
        "payment-cancel.html"
    )