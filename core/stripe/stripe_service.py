import os
import stripe
import traceback

from flask import redirect

from core.db.subscription_repository import (
    save_subscription
)

stripe.api_key = os.getenv(
    "STRIPE_SECRET_KEY"
)

BASE_URL = os.getenv(
    "BASE_URL",
    "http://127.0.0.1:5000"
)

# =========================================
# CREATE CHECKOUT SESSION
# =========================================

def create_checkout_session(
    customer_email
):

    price_id = os.getenv(
        "STRIPE_PRICE_ID"
    )

    return stripe.checkout.Session.create(

        mode="subscription",

        customer_email=customer_email,

        payment_method_collection="always",

        line_items=[{
            "price": price_id,
            "quantity": 1
        }],

        subscription_data={
            "trial_period_days": 7
        },

        success_url=(

            f"{BASE_URL}/success"
            "?session_id={CHECKOUT_SESSION_ID}"
        ),

        cancel_url=(

            f"{BASE_URL}/payment-cancel"
        )
    )

# =========================================
# HANDLE SUCCESS
# =========================================

def handle_success(session_id):

    try:

        print(
            f"[STRIPE SUCCESS] session_id={session_id}"
        )

        if not session_id:

            return redirect("/app")

        checkout_session = (
            stripe.checkout.Session.retrieve(
                session_id
            )
        )

        subscription_id = (
            checkout_session.subscription
        )

        customer_id = (
            checkout_session.customer
        )

        customer_email = None

        try:

            if (
                hasattr(
                    checkout_session,
                    "customer_details"
                )
                and checkout_session.customer_details
            ):

                customer_email = (
                    checkout_session
                    .customer_details
                    .email
                )

        except Exception:
            pass

        if not customer_email:

            try:

                customer_email = (
                    checkout_session
                    .customer_email
                )

            except Exception:
                pass

        subscription = (
            stripe.Subscription.retrieve(
                subscription_id
            )
        )

        current_period_end = None

        try:

            if (
                hasattr(subscription, "_data")
                and isinstance(
                    subscription._data,
                    dict
                )
            ):

                current_period_end = (
                    subscription._data.get(
                        "current_period_end",
                        None
                    )
                )

        except Exception:

            current_period_end = None

        save_subscription(

            email=customer_email,

            customer_id=customer_id,

            subscription_id=subscription_id,

            status=subscription.status,

            plan="premium",

            current_period_end=current_period_end
        )

        return redirect(
            "/app?payment=success"
        )

    except Exception as e:

        print(
            "[SUCCESS ROUTE ERROR]"
        )

        print(e)

        traceback.print_exc()

        return redirect(
            "/app?payment=failed"
        )