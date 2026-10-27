import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, current_app, jsonify
from app.models import db, Order, Listing, PaymentRecord, User
from app.utils.auth import login_required, get_current_user
from app.utils.payment import is_razorpay_configured, create_razorpay_order, verify_razorpay_signature, process_demo_escrow_payment, get_payment_disclaimer

orders_bp = Blueprint("orders", __name__)

@orders_bp.route("/orders")
@login_required
def index():
    """List of all orders for the current student (both purchases and sales)."""
    user = get_current_user()
    tab = request.args.get("tab", "purchases")

    purchases = Order.query.filter_by(buyer_id=user.id).order_by(Order.created_at.desc()).all()
    sales = Order.query.filter_by(seller_id=user.id).order_by(Order.created_at.desc()).all()

    return render_template(
        "orders/index.html",
        purchases=purchases,
        sales=sales,
        active_tab=tab,
        current_user=user
    )

@orders_bp.route("/orders/checkout/<int:listing_id>", methods=["GET", "POST"])
@login_required
def checkout(listing_id):
    """Checkout page for initiating purchase with Demo Escrow or Razorpay Test Mode."""
    listing = Listing.query.get_or_404(listing_id)
    user = get_current_user()

    if listing.seller_id == user.id:
        flash("You cannot purchase your own listing.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    if listing.status != "Available":
        flash(f"This listing is currently {listing.status.lower()} and not available for checkout.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing.id))

    razorpay_enabled = is_razorpay_configured()
    disclaimer = get_payment_disclaimer()

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "DEMO_ESCROW")
        pickup_location = request.form.get("pickup_location", "").strip() or listing.pickup_area
        notes = request.form.get("notes", "").strip()

        # Generate unique order number
        order_number = f"SM-ORD-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        new_order = Order(
            order_number=order_number,
            listing_id=listing.id,
            buyer_id=user.id,
            seller_id=listing.seller_id,
            amount=listing.price,
            status="PENDING",
            payment_method=payment_method,
            pickup_location=pickup_location,
            notes=notes
        )
        db.session.add(new_order)
        listing.status = "Reserved"
        db.session.commit()

        if payment_method == "DEMO_ESCROW":
            # Simulate immediate campus demo escrow hold
            process_demo_escrow_payment(new_order)
            flash(f"Order #{new_order.order_number} placed successfully! Funds are held in demo escrow until campus inspection.", "success")
            return redirect(url_for("orders.detail", order_id=new_order.id))

        elif payment_method == "RAZORPAY_TEST" and razorpay_enabled:
            # Handle Razorpay test order initiation
            rp_order = create_razorpay_order(new_order)
            if rp_order:
                return render_template(
                    "orders/razorpay_pay.html",
                    order=new_order,
                    rp_order=rp_order,
                    razorpay_key=current_app.config["RAZORPAY_KEY_ID"],
                    current_user=user
                )
            else:
                flash("Razorpay test gateway encountered an issue. Falling back to Demo Escrow.", "warning")
                process_demo_escrow_payment(new_order)
                return redirect(url_for("orders.detail", order_id=new_order.id))
        else:
            # Default fallback to demo escrow
            process_demo_escrow_payment(new_order)
            flash("Campus safe demo escrow confirmed.", "success")
            return redirect(url_for("orders.detail", order_id=new_order.id))

    return render_template(
        "orders/checkout.html",
        listing=listing,
        razorpay_enabled=razorpay_enabled,
        disclaimer=disclaimer,
        current_user=user
    )

@orders_bp.route("/orders/<int:order_id>")
@login_required
def detail(order_id):
    """View order status timeline and authorized state actions."""
    order = Order.query.get_or_404(order_id)
    user = get_current_user()

    # Access check: buyer, seller or admin only
    if user.id not in (order.buyer_id, order.seller_id) and not user.is_admin:
        abort(403)

    is_buyer = (user.id == order.buyer_id)
    is_seller = (user.id == order.seller_id)

    return render_template(
        "orders/detail.html",
        order=order,
        is_buyer=is_buyer,
        is_seller=is_seller,
        disclaimer=get_payment_disclaimer(),
        current_user=user
    )

@orders_bp.route("/orders/<int:order_id>/action", methods=["POST"])
@login_required
def update_status(order_id):
    """Enforce authorized order state transitions."""
    order = Order.query.get_or_404(order_id)
    user = get_current_user()

    action = request.form.get("action")
    if not action:
        flash("Invalid action specified.", "warning")
        return redirect(url_for("orders.detail", order_id=order.id))

    # Check state machine permission
    if not order.can_transition_to(action, user.id) and not user.is_admin:
        flash("You are not authorized to perform this transition on this order.", "danger")
        return redirect(url_for("orders.detail", order_id=order.id))

    if action == "ACCEPTED":
        order.status = "ACCEPTED"
        flash("Order accepted! Please coordinate with the buyer for campus meeting.", "success")

    elif action == "COMPLETED":
        order.status = "COMPLETED"
        order.payment_status = "RELEASED_TO_SELLER"
        order.listing.status = "Sold"
        flash("Order completed! Item marked as Sold and escrow released.", "success")

    elif action == "CANCELLED":
        order.status = "CANCELLED"
        order.payment_status = "REFUNDED"
        order.listing.status = "Available"
        flash("Order cancelled. Listing returned to Available status.", "info")

    db.session.commit()
    return redirect(url_for("orders.detail", order_id=order.id))

@orders_bp.route("/orders/<int:order_id>/dispute", methods=["POST"])
@login_required
def raise_dispute(order_id):
    """Submit a dispute regarding item quality, non-appearance, or other issues."""
    order = Order.query.get_or_404(order_id)
    user = get_current_user()

    if user.id not in (order.buyer_id, order.seller_id) and not user.is_admin:
        abort(403)

    reason = request.form.get("dispute_reason", "").strip()
    if not reason:
        flash("Please explain the reason for raising a dispute.", "warning")
        return redirect(url_for("orders.detail", order_id=order.id))

    order.status = "DISPUTED"
    order.dispute_reason = reason
    db.session.commit()

    flash("Dispute raised. The administration team will review the transaction and communicate with both parties.", "warning")
    return redirect(url_for("orders.detail", order_id=order.id))

@orders_bp.route("/orders/razorpay-verify", methods=["POST"])
@login_required
def razorpay_verify():
    """Server-side verification of Razorpay payment signature."""
    order_id = request.form.get("order_id", type=int)
    rp_order_id = request.form.get("razorpay_order_id")
    rp_payment_id = request.form.get("razorpay_payment_id")
    rp_signature = request.form.get("razorpay_signature")

    order = Order.query.get_or_404(order_id)
    user = get_current_user()

    if user.id != order.buyer_id:
        abort(403)

    is_valid = verify_razorpay_signature(rp_order_id, rp_payment_id, rp_signature)

    if is_valid:
        payment_record = PaymentRecord(
            order_id=order.id,
            gateway="RAZORPAY_TEST",
            gateway_order_id=rp_order_id,
            gateway_payment_id=rp_payment_id,
            gateway_signature=rp_signature,
            amount=order.amount,
            currency="INR",
            status="HELD_IN_ESCROW",
            is_verified=True,
            verification_notes="Verified via Razorpay HMAC-SHA256 signature."
        )
        order.payment_status = "HELD_IN_ESCROW"
        order.payment_method = "RAZORPAY_TEST"
        db.session.add(payment_record)
        db.session.commit()

        flash("Razorpay payment verified successfully! Escrow hold activated.", "success")
        return redirect(url_for("orders.detail", order_id=order.id))
    else:
        flash("Payment signature verification failed. Please contact support.", "danger")
        return redirect(url_for("orders.checkout", listing_id=order.listing_id))
