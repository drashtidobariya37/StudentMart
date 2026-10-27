import secrets
import hmac
from flask import session, request, abort, current_app

def generate_csrf_token():
    """Generates and stores a CSRF token in the session if not present."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]

def validate_csrf():
    """Validates CSRF token for state-changing HTTP requests."""
    # Skip CSRF check in testing mode or for safe read-only methods
    if current_app.config.get("TESTING") or request.method in ("GET", "HEAD", "OPTIONS"):
        return

    # Extract token from form data or HTTP header
    submitted_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    session_token = session.get("_csrf_token")

    if not session_token or not submitted_token:
        abort(400, description="Missing CSRF security token. Please refresh the page and try again.")

    if not hmac.compare_digest(submitted_token, session_token):
        abort(400, description="Invalid CSRF token. Request rejected for security.")
