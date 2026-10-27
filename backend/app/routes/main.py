from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from app.models import db, Listing, College, ContactMessage, User, UrgentRequest, Notification
from app.utils.auth import get_current_user, login_required
from app.utils.security import rate_limiter, get_client_ip

main_bp = Blueprint("main", __name__)

GUJARAT_CITIES = [
    {"name": "Ahmedabad", "tagline": "Gujarat's student & tech innovation hub", "badge": "Primary Campus Hub"},
    {"name": "Gandhinagar", "tagline": "Capital knowledge corridor (DA-IICT, IITGn, PDEU)", "badge": "Education City"},
    {"name": "Surat", "tagline": "South Gujarat engineering & design corridor (SVNIT)", "badge": "Tech Zone"},
    {"name": "Vadodara", "tagline": "Cultural capital & prestigious university campus (MSU)", "badge": "Heritage Hub"},
    {"name": "Rajkot", "tagline": "Saurashtra university & engineering cluster", "badge": "Regional Hub"},
    {"name": "Anand", "tagline": "Vidyanagar education township & research institutes", "badge": "Campus Town"},
    {"name": "Mehsana", "tagline": "North Gujarat engineering colleges", "badge": "Emerging"},
    {"name": "Bhavnagar", "tagline": "Coastal Gujarat universities", "badge": "Regional"}
]

@main_bp.route("/")
def index():
    """
    Marketplace homepage with Gujarat priority (Ahmedabad & Gandhinagar spotlight),
    functional Urgent Need feed, category discovery, campus verification, and India-wide access.
    """
    now = datetime.utcnow()
    user = get_current_user()

    # Active session location (default Gujarat / Ahmedabad)
    current_state = session.get("location_state") or (user.preferred_state if user else "Gujarat")
    current_city = session.get("location_city") or (user.preferred_city if user else "Ahmedabad")

    # 1. Urgent Needs Spotlight (prioritizing Ahmedabad & Gandhinagar active requests)
    urgent_requests = UrgentRequest.query.filter(
        UrgentRequest.status == "Active",
        UrgentRequest.expires_at > now,
        UrgentRequest.moderation_status == "Approved"
    ).order_by(UrgentRequest.expires_at.asc()).limit(6).all()

    # 2. Ahmedabad & Gandhinagar Listings
    ahmedabad_listings = Listing.query.filter(
        Listing.city == "Ahmedabad",
        Listing.status == "Available",
        Listing.moderation_status == "Approved"
    ).order_by(Listing.created_at.desc()).limit(4).all()

    gandhinagar_listings = Listing.query.filter(
        Listing.city == "Gandhinagar",
        Listing.status == "Available",
        Listing.moderation_status == "Approved"
    ).order_by(Listing.created_at.desc()).limit(4).all()

    # 3. All Gujarat Featured Listings
    gujarat_listings = Listing.query.filter(
        Listing.state == "Gujarat",
        Listing.status == "Available",
        Listing.moderation_status == "Approved"
    ).order_by(Listing.view_count.desc(), Listing.created_at.desc()).limit(8).all()

    # 4. India-wide Recent Listings
    recent_listings = Listing.query.filter(
        Listing.status == "Available",
        Listing.moderation_status == "Approved"
    ).order_by(Listing.created_at.desc()).limit(8).all()

    # Real-time statistics from actual database
    total_listings = Listing.query.filter_by(moderation_status="Approved", status="Available").count()
    gujarat_listings_count = Listing.query.filter_by(state="Gujarat", moderation_status="Approved", status="Available").count()
    ahmedabad_count = Listing.query.filter_by(city="Ahmedabad", moderation_status="Approved", status="Available").count()
    gandhinagar_count = Listing.query.filter_by(city="Gandhinagar", moderation_status="Approved", status="Available").count()
    active_urgent_count = UrgentRequest.query.filter(UrgentRequest.status == "Active", UrgentRequest.expires_at > now, UrgentRequest.moderation_status == "Approved").count()

    colleges = College.query.order_by(College.name).all()
    colleges_count = len(colleges)
    users_count = User.query.filter_by(is_active=True).count()

    # Category counts
    categories = [
        {"name": "Books & Study Notes", "icon": "bi-book", "desc": "Engineering textbooks, semester notes & question banks", "count": Listing.query.filter_by(category="Books & Study Notes", status="Available").count()},
        {"name": "Electronics & Laptops", "icon": "bi-laptop", "desc": "Monitors, keyboards, Arduino kits & chargers", "count": Listing.query.filter_by(category="Electronics & Laptops", status="Available").count()},
        {"name": "Lab Equipment & Coats", "icon": "bi-eyeglasses", "desc": "White lab coats, safety goggles, multimeters & tools", "count": Listing.query.filter_by(category="Lab Equipment & Coats", status="Available").count()},
        {"name": "Scientific Calculators", "icon": "bi-calculator", "desc": "Casio fx-991EX, fx-82MS & non-programmable calcs", "count": Listing.query.filter_by(category="Scientific Calculators", status="Available").count()},
        {"name": "Hostel Essentials & Appliances", "icon": "bi-cup-hot", "desc": "Kettles, study lamps, bed sheets & dorm organizers", "count": Listing.query.filter_by(category="Hostel Essentials & Appliances", status="Available").count()},
        {"name": "Engineering Drawing & Tools", "icon": "bi-pencil-ruler", "desc": "Mini drafters, drawing sheets & T-squares", "count": Listing.query.filter_by(category="Engineering Drawing & Tools", status="Available").count()},
        {"name": "Cycles & Campus Mobility", "icon": "bi-bicycle", "desc": "Hostel campus bicycles & safety cable locks", "count": Listing.query.filter_by(category="Cycles & Campus Mobility", status="Available").count()},
        {"name": "Miscellaneous", "icon": "bi-grid", "desc": "College merchandise, bags, sports gear & stationery", "count": Listing.query.filter_by(category="Miscellaneous", status="Available").count()},
    ]

    return render_template(
        "index.html",
        urgent_requests=urgent_requests,
        ahmedabad_listings=ahmedabad_listings,
        gandhinagar_listings=gandhinagar_listings,
        gujarat_listings=gujarat_listings,
        recent_listings=recent_listings,
        gujarat_cities=GUJARAT_CITIES,
        categories=categories,
        colleges=colleges,
        colleges_count=colleges_count,
        total_listings=total_listings,
        gujarat_listings_count=gujarat_listings_count,
        ahmedabad_count=ahmedabad_count,
        gandhinagar_count=gandhinagar_count,
        active_urgent_count=active_urgent_count,
        users_count=users_count,
        current_state=current_state,
        current_city=current_city,
        current_user=user
    )


@main_bp.route("/set-location", methods=["POST"])
def set_location():
    """Update active browsing location in session and user profile if logged in."""
    state = request.form.get("state", "Gujarat").strip()
    city = request.form.get("city", "").strip()

    session["location_state"] = state
    session["location_city"] = city

    user = get_current_user()
    if user:
        if state:
            user.preferred_state = state
        if city:
            user.preferred_city = city
        db.session.commit()

    if request.is_json:
        return jsonify({"success": True, "state": state, "city": city})

    flash(f"Browsing location set to {city or state}!", "info")
    return redirect(request.referrer or url_for("main.index"))


@main_bp.route("/notifications")
@login_required
def notifications():
    """List student alerts and activity updates."""
    user = get_current_user()
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return render_template("notifications.html", notifications=notifs, current_user=user)


@main_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    """Mark all unread notifications as read."""
    user = get_current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("main.notifications"))


@main_bp.route("/notifications/<int:notif_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notif_id):
    """Mark a single notification as read and follow its link."""
    user = get_current_user()
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != user.id:
        abort(403)
    notif.is_read = True
    db.session.commit()
    return redirect(notif.link or url_for("main.notifications"))


@main_bp.route("/about")
def about():
    """About page outlining the project background, architecture, and mission."""
    return render_template("about.html", current_user=get_current_user())


@main_bp.route("/safety")
def safety():
    """Safety Centre: Campus meetup guidelines, scam prevention, and prohibited items list."""
    colleges = College.query.all()
    return render_template("safety.html", colleges=colleges, current_user=get_current_user())


@main_bp.route("/terms")
def terms():
    """Terms of Service, dispute policies, and marketplace conduct guidelines."""
    return render_template("terms.html", current_user=get_current_user())


@main_bp.route("/privacy")
def privacy():
    """Student privacy policy highlighting minimal data collection and no public phone exposure."""
    return render_template("privacy.html", current_user=get_current_user())


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact & support inquiry submission with rate limiting."""
    if request.method == "POST":
        ip = get_client_ip()
        if not rate_limiter.is_allowed(f"contact_{ip}", max_requests=5, window_seconds=60):
            flash("Too many messages submitted from this connection. Please wait a minute before trying again.", "danger")
            return redirect(url_for("main.contact"))

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        college = request.form.get("college", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not subject or not message:
            flash("Please complete all required fields.", "warning")
            return redirect(url_for("main.contact"))

        contact_msg = ContactMessage(
            name=name,
            email=email,
            college=college,
            subject=subject,
            message=message
        )
        db.session.add(contact_msg)
        db.session.commit()

        flash("Thank you for reaching out! A campus coordinator will reply to your student email soon.", "success")
        return redirect(url_for("main.contact"))

    return render_template("contact.html", current_user=get_current_user())
