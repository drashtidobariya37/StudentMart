from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from app.models import db, User, Listing, Order, Report, ContactMessage, College, UrgentRequest
from app.utils.auth import login_required, admin_required, get_current_user

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
@login_required
@admin_required
def admin_protect():
    """Protects all admin endpoints from non-administrators."""
    pass

@admin_bp.route("/")
def dashboard():
    """Main administrative dashboard with platform metrics and quick queues."""
    total_users = User.query.count()
    total_listings = Listing.query.count()
    active_listings = Listing.query.filter_by(status="Available", moderation_status="Approved").count()
    total_urgent = UrgentRequest.query.count()
    active_urgent = UrgentRequest.query.filter_by(status="Active", moderation_status="Approved").count()
    pending_reports = Report.query.filter_by(status="PENDING").count()
    disputed_orders = Order.query.filter_by(status="DISPUTED").count()
    total_orders = Order.query.count()
    
    # Recent activity
    recent_reports = Report.query.order_by(Report.created_at.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_listings = Listing.query.order_by(Listing.created_at.desc()).limit(5).all()
    recent_urgent = UrgentRequest.query.order_by(UrgentRequest.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_listings=total_listings,
        active_listings=active_listings,
        total_urgent=total_urgent,
        active_urgent=active_urgent,
        pending_reports=pending_reports,
        disputed_orders=disputed_orders,
        total_orders=total_orders,
        recent_reports=recent_reports,
        recent_orders=recent_orders,
        recent_listings=recent_listings,
        recent_urgent=recent_urgent,
        current_user=get_current_user()
    )

@admin_bp.route("/listings")
def listings():
    """Listing moderation queue."""
    status_filter = request.args.get("status")
    query = Listing.query

    if status_filter:
        query = query.filter_by(moderation_status=status_filter)

    all_listings = query.order_by(Listing.created_at.desc()).all()
    return render_template("admin/listings.html", listings=all_listings, selected_status=status_filter, current_user=get_current_user())

@admin_bp.route("/listings/<int:listing_id>/moderate", methods=["POST"])
def moderate_listing(listing_id):
    """Update moderation status of a listing (Approved, Flagged, Rejected)."""
    listing = Listing.query.get_or_404(listing_id)
    action = request.form.get("action")

    if action in ["Approved", "Flagged", "Rejected"]:
        listing.moderation_status = action
        if action == "Rejected":
            listing.status = "Hidden"
        db.session.commit()
        flash(f"Listing #{listing.id} status updated to {action}.", "success")

    return redirect(request.referrer or url_for("admin.listings"))

@admin_bp.route("/urgent")
def urgent():
    """Urgent Need moderation queue."""
    status_filter = request.args.get("status")
    query = UrgentRequest.query

    if status_filter:
        query = query.filter_by(moderation_status=status_filter)

    all_urgent = query.order_by(UrgentRequest.created_at.desc()).all()
    return render_template("admin/urgent.html", urgent_requests=all_urgent, selected_status=status_filter, current_user=get_current_user())

@admin_bp.route("/urgent/<int:request_id>/moderate", methods=["POST"])
def moderate_urgent(request_id):
    """Update moderation status of an urgent request (Approved, Flagged, Rejected)."""
    req = UrgentRequest.query.get_or_404(request_id)
    action = request.form.get("action")

    if action in ["Approved", "Flagged", "Rejected"]:
        req.moderation_status = action
        if action == "Rejected":
            req.status = "Cancelled"
        db.session.commit()
        flash(f"Urgent Request #{req.id} moderation status updated to {action}.", "success")

    return redirect(request.referrer or url_for("admin.urgent"))

@admin_bp.route("/reports")
def reports():
    """Trust & Safety user reports queue."""
    all_reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template("admin/reports.html", reports=all_reports, current_user=get_current_user())

@admin_bp.route("/reports/<int:report_id>/resolve", methods=["POST"])
def resolve_report(report_id):
    """Take action on a reported item, urgent request, or user."""
    report = Report.query.get_or_404(report_id)
    action = request.form.get("action")
    admin_notes = request.form.get("admin_notes", "").strip()

    report.admin_notes = admin_notes
    if action == "DISMISS":
        report.status = "DISMISSED"
        flash("Report dismissed with no action required.", "info")
    elif action == "HIDE_LISTING":
        report.status = "ACTION_TAKEN"
        if report.listing:
            report.listing.moderation_status = "Rejected"
            report.listing.status = "Hidden"
        if report.urgent_request:
            report.urgent_request.moderation_status = "Rejected"
            report.urgent_request.status = "Cancelled"
        flash("Report resolved. Item hidden from marketplace.", "success")
    elif action == "SUSPEND_USER":
        report.status = "ACTION_TAKEN"
        if report.reported_user:
            report.reported_user.is_active = False
        flash("Report resolved. Reported user account suspended.", "danger")

    db.session.commit()
    return redirect(url_for("admin.reports"))

@admin_bp.route("/orders")
def orders():
    """Orders & Disputes management."""
    status_filter = request.args.get("status")
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    all_orders = query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=all_orders, selected_status=status_filter, current_user=get_current_user())

@admin_bp.route("/orders/<int:order_id>/resolve_dispute", methods=["POST"])
def resolve_dispute(order_id):
    """Admin dispute resolution."""
    order = Order.query.get_or_404(order_id)
    resolution_action = request.form.get("resolution")
    resolution_notes = request.form.get("resolution_notes", "").strip()

    order.dispute_resolution = resolution_notes
    if resolution_action == "REFUND_BUYER":
        order.status = "CANCELLED"
        order.payment_status = "REFUNDED"
        order.listing.status = "Available"
        flash(f"Dispute resolved. Refund approved for Buyer ({order.buyer.display_name}).", "info")
    elif resolution_action == "RELEASE_SELLER":
        order.status = "COMPLETED"
        order.payment_status = "RELEASED_TO_SELLER"
        order.listing.status = "Sold"
        flash(f"Dispute resolved. Escrow released to Seller ({order.seller.display_name}).", "success")

    db.session.commit()
    return redirect(url_for("admin.orders"))

@admin_bp.route("/users")
def users():
    """Student accounts directory."""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users, current_user=get_current_user())

@admin_bp.route("/users/<int:user_id>/toggle_verify", methods=["POST"])
def toggle_verify_user(user_id):
    """Toggles student verification badge."""
    user = User.query.get_or_404(user_id)
    user.is_verified_student = not user.is_verified_student
    db.session.commit()
    status_str = "Verified" if user.is_verified_student else "Unverified"
    flash(f"Student verification for {user.display_name} updated to {status_str}.", "info")
    return redirect(url_for("admin.users"))

@admin_bp.route("/contacts")
def contacts():
    """Contact messages received from website visitors."""
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/contacts.html", messages=messages, current_user=get_current_user())
