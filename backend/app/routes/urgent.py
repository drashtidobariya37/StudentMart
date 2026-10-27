from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from app.models import db, UrgentRequest, UrgentOffer, Notification, College, Report
from app.utils.auth import login_required, get_current_user
from app.utils.security import save_upload_image, rate_limiter, get_client_ip

urgent_bp = Blueprint("urgent", __name__)

GUJARAT_CITIES = [
    "Ahmedabad", "Gandhinagar", "Surat", "Vadodara", "Rajkot", "Anand", "Mehsana", "Bhavnagar"
]

ALL_INDIAN_STATES = [
    "Gujarat", "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana",
    "Uttar Pradesh", "Rajasthan", "Madhya Pradesh", "West Bengal", "Punjab", "Haryana",
    "Kerala", "Andhra Pradesh", "Bihar", "Odisha", "Assam", "Goa", "Uttarakhand"
]

CATEGORIES = [
    "Textbooks & Reference",
    "Handwritten Notes",
    "Scientific Calculators",
    "Lab Equipment & Coats",
    "Electronics & Chargers",
    "Drafting & Stationery",
    "Project Components",
    "Hostel Essentials",
    "Other"
]

URGENCY_TIERS = [
    "Within 1 hour",
    "Today",
    "Tomorrow",
    "Flexible"
]


@urgent_bp.route("/urgent")
def feed():
    """Public urgent requests feed with location and category filters."""
    # Read search & filter parameters
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    urgency = request.args.get("urgency", "").strip()
    state = request.args.get("state", "").strip()
    city = request.args.get("city", "").strip()
    status_filter = request.args.get("status", "Active").strip()

    # Default location from session if not provided
    if not state and not city and not request.args.get("all_locations"):
        state = session.get("location_state", "Gujarat")
        city = session.get("location_city", "")

    # Base query for approved requests
    query = UrgentRequest.query.filter_by(moderation_status="Approved")

    now = datetime.utcnow()

    # Status filter
    if status_filter == "Active":
        query = query.filter(UrgentRequest.status == "Active", UrgentRequest.expires_at > now)
    elif status_filter == "Fulfilled":
        query = query.filter(UrgentRequest.status == "Fulfilled")
    elif status_filter == "Expired":
        query = query.filter((UrgentRequest.status == "Expired") | ((UrgentRequest.status == "Active") & (UrgentRequest.expires_at <= now)))
    elif status_filter != "All":
        query = query.filter(UrgentRequest.status == status_filter)

    # Search keyword
    if q:
        search_pattern = f"%{q}%"
        query = query.filter(
            (UrgentRequest.title.ilike(search_pattern)) | 
            (UrgentRequest.description.ilike(search_pattern)) |
            (UrgentRequest.preferred_pickup.ilike(search_pattern))
        )

    # Category filter
    if category and category != "All":
        query = query.filter(UrgentRequest.category == category)

    # Urgency filter
    if urgency and urgency != "All":
        query = query.filter(UrgentRequest.urgency == urgency)

    # State filter
    if state and state != "All":
        query = query.filter(UrgentRequest.state == state)

    # City filter
    if city and city != "All":
        query = query.filter(UrgentRequest.city == city)

    # Order by expiry time ascending so most urgent appears first
    requests_list = query.order_by(UrgentRequest.expires_at.asc()).all()

    # Fetch live counts for Gujarat cities and India
    ahmedabad_count = UrgentRequest.query.filter(
        UrgentRequest.status == "Active",
        UrgentRequest.expires_at > now,
        UrgentRequest.city == "Ahmedabad",
        UrgentRequest.moderation_status == "Approved"
    ).count()

    gandhinagar_count = UrgentRequest.query.filter(
        UrgentRequest.status == "Active",
        UrgentRequest.expires_at > now,
        UrgentRequest.city == "Gandhinagar",
        UrgentRequest.moderation_status == "Approved"
    ).count()

    surat_count = UrgentRequest.query.filter(
        UrgentRequest.status == "Active",
        UrgentRequest.expires_at > now,
        UrgentRequest.city == "Surat",
        UrgentRequest.moderation_status == "Approved"
    ).count()

    vadodara_count = UrgentRequest.query.filter(
        UrgentRequest.status == "Active",
        UrgentRequest.expires_at > now,
        UrgentRequest.city == "Vadodara",
        UrgentRequest.moderation_status == "Approved"
    ).count()

    gujarat_total = UrgentRequest.query.filter(
        UrgentRequest.status == "Active",
        UrgentRequest.expires_at > now,
        UrgentRequest.state == "Gujarat",
        UrgentRequest.moderation_status == "Approved"
    ).count()

    all_india_count = UrgentRequest.query.filter(
        UrgentRequest.status == "Active",
        UrgentRequest.expires_at > now,
        UrgentRequest.moderation_status == "Approved"
    ).count()

    colleges = College.query.order_by(College.name.asc()).all()

    return render_template(
        "urgent/index.html",
        requests=requests_list,
        categories=CATEGORIES,
        urgency_tiers=URGENCY_TIERS,
        gujarat_cities=GUJARAT_CITIES,
        all_states=ALL_INDIAN_STATES,
        colleges=colleges,
        selected_category=category,
        selected_urgency=urgency,
        selected_state=state,
        selected_city=city,
        selected_status=status_filter,
        search_query=q,
        ahmedabad_count=ahmedabad_count,
        gandhinagar_count=gandhinagar_count,
        surat_count=surat_count,
        vadodara_count=vadodara_count,
        gujarat_total=gujarat_total,
        all_india_count=all_india_count
    )


@urgent_bp.route("/urgent/create", methods=["GET", "POST"])
@login_required
def create():
    """Create a new urgent item request."""
    user = get_current_user()

    if request.method == "POST":
        ip = get_client_ip()
        if not rate_limiter.is_allowed(f"urgent_create_{ip}_{user.id}", max_requests=10, window_seconds=60):
            flash("You are creating requests too quickly. Please pause a moment.", "danger")
            return redirect(url_for("urgent.create"))

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        urgency = request.form.get("urgency", "Today").strip()
        quantity_str = request.form.get("quantity", "1").strip()
        state = request.form.get("state", user.preferred_state or "Gujarat").strip()
        city = request.form.get("city", user.preferred_city or "Ahmedabad").strip()
        college_id_str = request.form.get("college_id", "").strip()
        college_name_custom = request.form.get("college_name_custom", "").strip()
        budget_str = request.form.get("budget", "").strip()
        preferred_pickup = request.form.get("preferred_pickup", "").strip()

        # Validation
        errors = []
        if len(title) < 5 or len(title) > 160:
            errors.append("Title must be between 5 and 160 characters.")
        if len(description) < 10:
            errors.append("Please provide a clearer description (at least 10 characters).")
        if category not in CATEGORIES:
            errors.append("Please select a valid category.")
        if urgency not in URGENCY_TIERS:
            errors.append("Please select a valid urgency level.")
        if not preferred_pickup:
            errors.append("Please specify a preferred campus pickup spot.")

        try:
            quantity = int(quantity_str)
            if quantity < 1:
                quantity = 1
        except ValueError:
            quantity = 1

        budget = None
        if budget_str:
            try:
                budget = int(budget_str)
                if budget < 0:
                    errors.append("Budget cannot be negative.")
            except ValueError:
                errors.append("Budget must be a valid number.")

        college_id = None
        if college_id_str:
            try:
                college_id = int(college_id_str)
            except ValueError:
                college_id = None

        # Image upload handling (optional reference photo)
        photo_path = None
        photo_file = request.files.get("photo")
        if photo_file and photo_file.filename:
            try:
                photo_path = save_upload_image(photo_file, subfolder="urgent")
            except ValueError as err:
                errors.append(str(err))

        if errors:
            for e in errors:
                flash(e, "danger")
            colleges = College.query.order_by(College.name.asc()).all()
            return render_template(
                "urgent/create.html",
                colleges=colleges,
                categories=CATEGORIES,
                urgency_tiers=URGENCY_TIERS,
                gujarat_cities=GUJARAT_CITIES,
                all_states=ALL_INDIAN_STATES,
                form_data=request.form
            )

        # Calculate expiry
        expires_at = UrgentRequest.calculate_expiry(urgency)

        urgent_req = UrgentRequest(
            user_id=user.id,
            college_id=college_id or user.college_id,
            college_name_custom=college_name_custom or (user.college.short_name if user.college else f"{city} Campus"),
            title=title,
            description=description,
            category=category,
            quantity=quantity,
            urgency=urgency,
            state=state,
            city=city,
            budget=budget,
            preferred_pickup=preferred_pickup,
            image_path=photo_path,
            status="Active",
            moderation_status="Approved",
            expires_at=expires_at
        )

        db.session.add(urgent_req)
        db.session.commit()

        flash("Your urgent need request has been posted to nearby campus students!", "success")
        return redirect(url_for("urgent.detail", request_id=urgent_req.id))

    colleges = College.query.order_by(College.name.asc()).all()
    return render_template(
        "urgent/create.html",
        colleges=colleges,
        categories=CATEGORIES,
        urgency_tiers=URGENCY_TIERS,
        gujarat_cities=GUJARAT_CITIES,
        all_states=ALL_INDIAN_STATES,
        form_data={}
    )


@urgent_bp.route("/urgent/<int:request_id>")
def detail(request_id):
    """View details of an urgent request and any offers."""
    req = UrgentRequest.query.get_or_404(request_id)
    user = get_current_user()

    # Check auto-expiry
    if req.status == "Active" and req.is_expired:
        req.status = "Expired"
        db.session.commit()

    is_owner = (user and user.id == req.user_id)
    user_existing_offer = None
    if user and not is_owner:
        user_existing_offer = UrgentOffer.query.filter_by(
            urgent_request_id=req.id,
            responder_id=user.id
        ).first()

    return render_template(
        "urgent/detail.html",
        urgent_req=req,
        is_owner=is_owner,
        user_existing_offer=user_existing_offer
    )


@urgent_bp.route("/urgent/<int:request_id>/offer", methods=["POST"])
@login_required
def submit_offer(request_id):
    """Submit a student help offer / response to an urgent request."""
    user = get_current_user()
    req = UrgentRequest.query.get_or_404(request_id)

    if req.user_id == user.id:
        flash("You cannot submit an offer on your own urgent request.", "warning")
        return redirect(url_for("urgent.detail", request_id=req.id))

    if req.effective_status != "Active":
        flash("This urgent request is no longer active.", "danger")
        return redirect(url_for("urgent.detail", request_id=req.id))

    message = request.form.get("message", "").strip()
    price_offered_str = request.form.get("price_offered", "").strip()
    is_free = (request.form.get("is_free_help") == "1" or request.form.get("is_free_help") == "on")
    pickup_suggestion = request.form.get("pickup_suggestion", "").strip()

    if len(message) < 5:
        flash("Please provide a helpful message describing how you can assist (min 5 chars).", "danger")
        return redirect(url_for("urgent.detail", request_id=req.id))

    price_offered = None
    if not is_free and price_offered_str:
        try:
            price_offered = int(price_offered_str)
            if price_offered < 0:
                flash("Offered price cannot be negative.", "danger")
                return redirect(url_for("urgent.detail", request_id=req.id))
        except ValueError:
            flash("Please enter a valid amount.", "danger")
            return redirect(url_for("urgent.detail", request_id=req.id))
    elif is_free:
        price_offered = 0

    # Save offer
    offer = UrgentOffer(
        urgent_request_id=req.id,
        responder_id=user.id,
        message=message,
        price_offered=price_offered,
        is_free_help=is_free,
        pickup_suggestion=pickup_suggestion or req.preferred_pickup
    )
    db.session.add(offer)

    # In-app notification for the requester
    notif = Notification(
        user_id=req.user_id,
        title=f"New Offer on '{req.title[:35]}'",
        message=f"{user.display_name} offered to help ({'Free help' if is_free else f'₹{price_offered}'})!",
        link=url_for("urgent.detail", request_id=req.id),
        category="urgent"
    )
    db.session.add(notif)
    db.session.commit()

    flash("Your offer has been submitted! The student has been notified.", "success")
    return redirect(url_for("urgent.detail", request_id=req.id))


@urgent_bp.route("/urgent/<int:request_id>/accept-offer/<int:offer_id>", methods=["POST"])
@login_required
def accept_offer(request_id, offer_id):
    """Requester accepts a student's offer."""
    user = get_current_user()
    req = UrgentRequest.query.get_or_404(request_id)

    if req.user_id != user.id:
        flash("Unauthorized action.", "danger")
        abort(403)

    offer = UrgentOffer.query.get_or_404(offer_id)
    if offer.urgent_request_id != req.id:
        flash("Invalid offer for this request.", "danger")
        return redirect(url_for("urgent.detail", request_id=req.id))

    offer.status = "Accepted"
    req.status = "Fulfilled"

    # Notify responder
    notif = Notification(
        user_id=offer.responder_id,
        title="Your Urgent Offer Was Accepted!",
        message=f"{user.display_name} accepted your offer for '{req.title[:35]}'. Meetup: {offer.pickup_suggestion or req.preferred_pickup}",
        link=url_for("urgent.detail", request_id=req.id),
        category="urgent"
    )
    db.session.add(notif)
    db.session.commit()

    flash(f"You accepted {offer.responder.display_name}'s offer! Request marked as Fulfilled.", "success")
    return redirect(url_for("urgent.detail", request_id=req.id))


@urgent_bp.route("/urgent/<int:request_id>/status", methods=["POST"])
@login_required
def update_status(request_id):
    """Toggle status between Active, Fulfilled, or Cancelled."""
    user = get_current_user()
    req = UrgentRequest.query.get_or_404(request_id)

    if req.user_id != user.id and not user.is_admin:
        abort(403)

    new_status = request.form.get("status", "").strip()
    if new_status in ["Active", "Fulfilled", "Cancelled"]:
        req.status = new_status
        db.session.commit()
        flash(f"Urgent request status updated to '{new_status}'.", "info")

    return redirect(url_for("urgent.detail", request_id=req.id))


@urgent_bp.route("/urgent/<int:request_id>/delete", methods=["POST"])
@login_required
def delete(request_id):
    """Delete an urgent request."""
    user = get_current_user()
    req = UrgentRequest.query.get_or_404(request_id)

    if req.user_id != user.id and not user.is_admin:
        abort(403)

    db.session.delete(req)
    db.session.commit()

    flash("Urgent request has been deleted.", "info")
    return redirect(url_for("urgent.feed"))


@urgent_bp.route("/urgent/<int:request_id>/report", methods=["POST"])
@login_required
def report(request_id):
    """Report an inappropriate or abusive urgent request."""
    user = get_current_user()
    req = UrgentRequest.query.get_or_404(request_id)

    reason = request.form.get("reason", "").strip()
    details = request.form.get("details", "").strip()

    if not reason or not details:
        flash("Please provide a reason and details for reporting.", "danger")
        return redirect(url_for("urgent.detail", request_id=req.id))

    new_report = Report(
        reporter_id=user.id,
        urgent_request_id=req.id,
        reported_user_id=req.user_id,
        reason=reason,
        details=details,
        status="PENDING"
    )
    db.session.add(new_report)
    db.session.commit()

    flash("Your report has been submitted to campus moderators for review.", "info")
    return redirect(url_for("urgent.detail", request_id=req.id))


@urgent_bp.route("/my-urgent")
@login_required
def my_urgent():
    """Dashboard showing current user's posted requests and submitted offers."""
    user = get_current_user()

    my_requests = UrgentRequest.query.filter_by(user_id=user.id).order_by(UrgentRequest.created_at.desc()).all()
    my_offers = UrgentOffer.query.filter_by(responder_id=user.id).order_by(UrgentOffer.created_at.desc()).all()

    return render_template(
        "urgent/my_urgent.html",
        my_requests=my_requests,
        my_offers=my_offers
    )
