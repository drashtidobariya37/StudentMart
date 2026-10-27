from functools import wraps
from flask import session, redirect, url_for, flash, request, abort, g
from app.models import User

def login_user(user):
    """Initializes user session upon successful login."""
    session.clear()
    session["user_id"] = user.id
    session["user_display_name"] = user.display_name
    session["user_is_admin"] = bool(user.is_admin)
    session.permanent = True
    g.current_user = user

def logout_user():
    """Clears the active session."""
    session.clear()
    g.current_user = None

def get_current_user():
    """Retrieves the current authenticated user instance from the database."""
    user_id = session.get("user_id")
    if not user_id:
        g.current_user = None
        return None

    if hasattr(g, "current_user") and g.current_user is not None:
        if getattr(g.current_user, "id", None) == user_id:
            return g.current_user

    from app.models import db
    user = db.session.get(User, user_id)
    if user and user.is_active:
        g.current_user = user
        return user
    else:
        # Invalid or deactivated session
        session.clear()
        g.current_user = None
        return None

def login_required(f):
    """Route decorator: Requires user to be logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Route decorator: Requires user to be an administrator."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user or not user.is_admin:
            flash("Administrator privileges are required to access this portal.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
