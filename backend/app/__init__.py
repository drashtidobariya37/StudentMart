import os
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, session, send_from_directory
from app.config import config_by_name, DevelopmentConfig
from app.models import db, Conversation, Message, Notification, ensure_schema_upgrades
from app.utils.csrf import generate_csrf_token, validate_csrf
from app.utils.auth import get_current_user

# Project root = student_mart/ (two levels up from backend/app/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_FRONTEND_DIR = _PROJECT_ROOT / "frontend"

def create_app(config_name=None):
    """Application factory for Student Mart."""
    app = Flask(
        __name__,
        template_folder=str(_FRONTEND_DIR / "templates"),
        static_folder=str(_FRONTEND_DIR / "static"),
        static_url_path="/static"
    )

    # Load configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    
    app_config = config_by_name.get(config_name, DevelopmentConfig)
    app.config.from_object(app_config)

    # Ensure required runtime folders exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "listings"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "urgent"), exist_ok=True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "avatars"), exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)

    # Safely ensure tables & schema column additions exist
    # Guard: only run seed in main process, not Werkzeug reloader child processes
    _is_main_process = (os.environ.get("WERKZEUG_RUN_MAIN") == "true") or not os.environ.get("FLASK_DEBUG")
    with app.app_context():
        db.create_all()
        ensure_schema_upgrades(db.engine)
        if not app.config.get("TESTING") and _is_main_process:
            try:
                import sys as _sys
                _backend_dir = str(_PROJECT_ROOT / "backend")
                if _backend_dir not in _sys.path:
                    _sys.path.insert(0, _backend_dir)
                from seed_data import ensure_seed_data
                ensure_seed_data()
            except Exception as e:
                print(f"[INIT] Startup data notice: {e}")

    # Reverse proxy support (for deployment behind Render, Railway, Nginx, Cloudflare)
    try:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    except Exception:
        pass

    # Universal upload media serving (supports local static and external persistent volumes)
    @app.route("/static/uploads/<path:filename>")
    @app.route("/uploads/<path:filename>")
    def serve_uploaded_media(filename):
        upload_folder = app.config["UPLOAD_FOLDER"]
        return send_from_directory(upload_folder, filename)

    # Security: CSRF Validation on mutating HTTP methods
    app.before_request(validate_csrf)

    # Context Processors for Templates
    @app.context_processor
    def inject_global_template_vars():
        user = get_current_user()
        unread_count = 0
        unread_notifications = 0

        if user:
            # Count unread messages across all conversations
            user_conv_ids = [c.id for c in Conversation.query.filter(
                (Conversation.buyer_id == user.id) | (Conversation.seller_id == user.id)
            ).all()]
            if user_conv_ids:
                unread_count = Message.query.filter(
                    Message.conversation_id.in_(user_conv_ids),
                    Message.sender_id != user.id,
                    Message.is_read == False
                ).count()
            
            unread_notifications = Notification.query.filter_by(
                user_id=user.id,
                is_read=False
            ).count()

        # Session-aware location defaults: Gujarat & Ahmedabad prioritized
        selected_state = session.get("location_state")
        selected_city = session.get("location_city")
        if not selected_state:
            selected_state = (user.preferred_state if user and user.preferred_state else "Gujarat")
        if not selected_city:
            selected_city = (user.preferred_city if user and user.preferred_city else "Ahmedabad")

        return {
            "csrf_token": generate_csrf_token,
            "current_user": user,
            "unread_count": unread_count,
            "unread_notifications": unread_notifications,
            "selected_state": selected_state,
            "selected_city": selected_city,
            "marketplace_name": app.config.get("MARKETPLACE_NAME", "Student Mart"),
            "now": datetime.utcnow()
        }

    # Custom Jinja Template Filters
    @app.template_filter("currency_inr")
    def currency_inr(value):
        """Formats integer as Indian Rupee (₹)."""
        if value is None:
            return "₹ 0"
        try:
            val = int(value)
            return f"₹ {val:,}"
        except (ValueError, TypeError):
            return f"₹ {value}"

    @app.template_filter("time_ago")
    def time_ago(dt):
        """Returns human-readable relative time."""
        if not dt:
            return ""
        diff = datetime.utcnow() - dt
        seconds = diff.total_seconds()
        if seconds < 0:
            return "Just now"
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours}h ago"
        elif seconds < 604800:
            days = int(seconds // 86400)
            return f"{days}d ago"
        else:
            return dt.strftime("%b %d, %Y")

    # Register Blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.listings import listings_bp
    from app.routes.urgent import urgent_bp
    from app.routes.messages import messages_bp
    from app.routes.orders import orders_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(listings_bp)
    app.register_blueprint(urgent_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)

    # HTTP Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors.html", code=400, title="Bad Request", message=error.description or "Invalid request submitted."), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors.html", code=403, title="Access Prohibited", message="You do not have authorization to view this resource."), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors.html", code=404, title="Item or Page Not Found", message="The requested listing, conversation, or page does not exist or has been removed."), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors.html", code=500, title="Server Error", message="A technical issue occurred on the server. Please try again shortly."), 500

    return app
