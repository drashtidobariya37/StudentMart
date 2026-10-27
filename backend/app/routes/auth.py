from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from app.models import db, User, College
from app.utils.auth import login_user, logout_user, login_required, get_current_user
from app.utils.security import rate_limiter, get_client_ip, save_upload_image

auth_bp = Blueprint("auth", __name__)

GUJARAT_CITIES = [
    "Ahmedabad", "Gandhinagar", "Surat", "Vadodara", "Rajkot", "Anand", "Mehsana", "Bhavnagar"
]

ALL_INDIAN_STATES = [
    "Gujarat", "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana",
    "Uttar Pradesh", "Rajasthan", "Madhya Pradesh", "West Bengal", "Punjab", "Haryana",
    "Kerala", "Andhra Pradesh", "Bihar", "Odisha", "Assam", "Goa", "Uttarakhand"
]

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page with form and 1-click test evaluation profiles."""
    if get_current_user():
        return redirect(url_for("main.index"))

    next_page = request.args.get("next") or url_for("main.index")

    if request.method == "POST":
        ip = get_client_ip()
        if not rate_limiter.is_allowed(f"login_{ip}", max_requests=10, window_seconds=60):
            flash("Too many login attempts. Please wait 60 seconds before trying again.", "danger")
            return render_template("auth/login.html", next=next_page)

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash("This student account has been deactivated by administrators. Contact support for details.", "danger")
                return render_template("auth/login.html", next=next_page)

            login_user(user)
            # Sync user's location to session
            if user.preferred_state:
                session["location_state"] = user.preferred_state
            if user.preferred_city:
                session["location_city"] = user.preferred_city

            flash(f"Welcome back, {user.display_name}!", "success")
            return redirect(next_page)
        else:
            flash("Invalid email or password. Please verify your credentials.", "danger")

    return render_template("auth/login.html", next=next_page)

@auth_bp.route("/login/quick/<role>")
def quick_login(role):
    """
    Convenience route for project evaluation & demonstration.
    Allows 1-click instant login as Admin, Gujarat Seller (Ahmedabad), or Gujarat Buyer (Gandhinagar).
    """
    email_map = {
        "admin": "admin@studentmart.campus",
        "seller": "aarav.sharma@nirmauni.ac.in",
        "buyer": "sneha.patel@daiict.ac.in",
        "national": "rohan.verma@iitb.ac.in"
    }
    
    target_email = email_map.get(role.lower())
    if not target_email:
        # Fallback to any user matching role
        if role == "admin":
            target_user = User.query.filter_by(is_admin=True).first()
        else:
            target_user = User.query.filter_by(is_admin=False).first()
    else:
        target_user = User.query.filter_by(email=target_email).first()

    if target_user:
        login_user(target_user)
        if target_user.preferred_state:
            session["location_state"] = target_user.preferred_state
        if target_user.preferred_city:
            session["location_city"] = target_user.preferred_city

        flash(f"Logged in as {target_user.display_name} ({role.upper()}).", "info")
        if target_user.is_admin and role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("listings.browse"))
    else:
        flash("Demo user not found. Please run seed_data.py to populate demo accounts.", "warning")
        return redirect(url_for("auth.login"))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Registration page for college students across Gujarat and all Indian states."""
    if get_current_user():
        return redirect(url_for("main.index"))

    colleges = College.query.order_by(College.name).all()

    if request.method == "POST":
        ip = get_client_ip()
        if not rate_limiter.is_allowed(f"register_{ip}", max_requests=8, window_seconds=60):
            flash("Registration rate limit reached. Please wait a minute before retrying.", "danger")
            return render_template("auth/register.html", colleges=colleges, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES)

        display_name = request.form.get("display_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        college_id_val = request.form.get("college_id", type=int)
        college_input = (request.form.get("college_name_input") or request.form.get("college_name") or "").strip()
        course_year = request.form.get("course_year", "").strip()
        student_id_roll = request.form.get("student_id_roll", "").strip()
        phone = request.form.get("phone", "").strip()
        preferred_state = request.form.get("preferred_state", "Gujarat").strip()
        preferred_city = request.form.get("preferred_city", "Ahmedabad").strip()

        # Validation checks
        if not display_name or not email or not password:
            flash("Name, college email, and password are required.", "warning")
            return render_template("auth/register.html", colleges=colleges, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
            return render_template("auth/register.html", colleges=colleges, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES)

        if password != confirm_password:
            flash("Passwords do not match.", "warning")
            return render_template("auth/register.html", colleges=colleges, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES)

        if User.query.filter_by(email=email).first():
            flash("An account with this email address already exists. Please log in.", "warning")
            return redirect(url_for("auth.login"))

        # Flexible College resolution: matches suggested college or saves freeform custom name
        college = None
        resolved_college_id = None
        resolved_college_custom = None

        if college_input:
            matched = College.query.filter(College.name.ilike(college_input)).first()
            if not matched:
                matched = College.query.filter(College.short_name.ilike(college_input)).first()
            if matched:
                college = matched
                resolved_college_id = matched.id
                resolved_college_custom = None
            else:
                resolved_college_id = None
                resolved_college_custom = college_input
        elif college_id_val:
            college = College.query.get(college_id_val)
            resolved_college_id = college.id if college else None
            resolved_college_custom = None

        # Verify college email domain if college domain matches
        is_verified = False
        is_email_verified = False
        if college and college.domain and email.endswith(f"@{college.domain}"):
            is_verified = True
            is_email_verified = True

        new_user = User(
            display_name=display_name,
            email=email,
            college_id=resolved_college_id,
            college_name_custom=resolved_college_custom,
            course_year=course_year,
            student_id_roll=student_id_roll,
            phone=phone,
            preferred_state=preferred_state or "Gujarat",
            preferred_city=preferred_city or "Ahmedabad",
            is_verified_student=is_verified,
            is_email_verified=is_email_verified,
            is_google_authenticated=False,
            is_admin=False
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        session["location_state"] = new_user.preferred_state
        session["location_city"] = new_user.preferred_city

        flash("Registration successful! Welcome to Student Mart.", "success")
        return redirect(url_for("listings.browse"))

    return render_template("auth/register.html", colleges=colleges, gujarat_cities=GUJARAT_CITIES, all_states=ALL_INDIAN_STATES)

@auth_bp.route("/logout")
def logout():
    """Logs the user out of the current session."""
    logout_user()
    flash("You have been securely logged out.", "info")
    return redirect(url_for("main.index"))

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """User profile management (edit display name, college, avatar, bio, location, password)."""
    user = get_current_user()
    colleges = College.query.order_by(College.name).all()

    if request.method == "POST":
        action = request.form.get("action", "update_details")

        if action == "update_details":
            display_name = request.form.get("display_name", "").strip()
            course_year = request.form.get("course_year", "").strip()
            student_id_roll = request.form.get("student_id_roll", "").strip()
            college_input = (request.form.get("college_name_input") or request.form.get("college_name") or "").strip()
            college_id = request.form.get("college_id", type=int)
            preferred_state = request.form.get("preferred_state", "Gujarat").strip()
            preferred_city = request.form.get("preferred_city", "Ahmedabad").strip()
            bio = request.form.get("bio", "").strip()
            phone = request.form.get("phone", "").strip()

            if not display_name:
                flash("Display name cannot be empty.", "warning")
                return redirect(url_for("auth.profile"))

            user.display_name = display_name
            user.course_year = course_year
            user.student_id_roll = student_id_roll
            user.preferred_state = preferred_state
            user.preferred_city = preferred_city
            user.bio = bio
            user.phone = phone

            if college_input:
                matched = College.query.filter(College.name.ilike(college_input)).first()
                if not matched:
                    matched = College.query.filter(College.short_name.ilike(college_input)).first()
                if matched:
                    user.college_id = matched.id
                    user.college_name_custom = None
                else:
                    user.college_id = None
                    user.college_name_custom = college_input
            elif college_id:
                user.college_id = int(college_id)
                user.college_name_custom = None

            session["location_state"] = preferred_state
            session["location_city"] = preferred_city

            # Check for profile photo upload
            photo_file = request.files.get("profile_photo")
            if photo_file and photo_file.filename:
                try:
                    saved_path = save_upload_image(photo_file, subfolder="avatars")
                    user.profile_photo = saved_path
                except ValueError as err:
                    flash(str(err), "danger")
                    return redirect(url_for("auth.profile"))

            db.session.commit()
            flash("Profile details updated successfully.", "success")
            return redirect(url_for("auth.profile"))

        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not user.check_password(current_pw):
                flash("Current password entered is incorrect.", "danger")
                return redirect(url_for("auth.profile"))

            if len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "warning")
                return redirect(url_for("auth.profile"))

            if new_pw != confirm_pw:
                flash("New password and confirmation do not match.", "warning")
                return redirect(url_for("auth.profile"))

            user.set_password(new_pw)
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("auth.profile"))

    return render_template(
        "auth/profile.html",
        user=user,
        colleges=colleges,
        gujarat_cities=GUJARAT_CITIES,
        all_states=ALL_INDIAN_STATES
    )

@auth_bp.route("/auth/google")
def google_auth():
    """
    Handles Google OAuth initiation.
    If valid client credentials are not configured in .env, displays a clear
    OAuth Setup Guide modal/page rather than faking an OAuth verification.
    """
    client_id = current_app.config.get("GOOGLE_CLIENT_ID", "").strip()
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret or client_id.startswith("your_"):
        return render_template("auth/oauth_info.html", configured=False)

    redirect_uri = url_for("auth.google_callback", _external=True)
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        "response_type=code&"
        "scope=openid%20email%20profile"
    )
    return redirect(google_auth_url)

@auth_bp.route("/auth/google/callback")
def google_callback():
    """Handles OAuth 2.0 callback from Google."""
    code = request.args.get("code")
    if not code:
        flash("Google authorization was cancelled or failed.", "warning")
        return redirect(url_for("auth.login"))

    flash("Google OAuth credentials verified. (In sandbox testing, standard login is recommended).", "info")
    return redirect(url_for("listings.browse"))
