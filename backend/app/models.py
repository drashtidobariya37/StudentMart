from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text

db = SQLAlchemy()

class College(db.Model):
    """Represents a verified higher education campus in India."""
    __tablename__ = "colleges"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    short_name = db.Column(db.String(50), index=True, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=True)
    campus_zones = db.Column(db.Text, nullable=True)  # Comma-separated designated safe meeting spots
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship("User", back_populates="college", lazy="dynamic")
    listings = db.relationship("Listing", back_populates="college", lazy="dynamic")

    def __repr__(self):
        return f"<College {self.short_name}>"

    def get_safe_spots_list(self):
        if not self.campus_zones:
            return ["Central Library", "Main Student Canteen", "Hostel Gate 1", "Dean Academics Quadrangle"]
        return [spot.strip() for spot in self.campus_zones.split(",") if spot.strip()]


class User(db.Model):
    """User account model for verified college students and admins."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey("colleges.id"), nullable=True)
    college_name_custom = db.Column(db.String(150), nullable=True)
    course_year = db.Column(db.String(80), nullable=True)  # e.g., "B.Tech Computer Engg - 3rd Year"
    student_id_roll = db.Column(db.String(50), nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)  # Hidden publicly by default for privacy
    
    # Location preferences (default Gujarat / Ahmedabad)
    preferred_state = db.Column(db.String(100), default="Gujarat")
    preferred_city = db.Column(db.String(100), default="Ahmedabad")
    
    # Trust & Verification flags - distinct and transparent
    is_email_verified = db.Column(db.Boolean, default=False)
    is_google_authenticated = db.Column(db.Boolean, default=False)
    is_verified_student = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    college = db.relationship("College", back_populates="users")
    listings = db.relationship("Listing", back_populates="seller", cascade="all, delete-orphan", lazy="dynamic")
    urgent_requests = db.relationship("UrgentRequest", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    urgent_offers = db.relationship("UrgentOffer", back_populates="responder", cascade="all, delete-orphan", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    orders_bought = db.relationship("Order", foreign_keys="Order.buyer_id", back_populates="buyer", lazy="dynamic")
    orders_sold = db.relationship("Order", foreign_keys="Order.seller_id", back_populates="seller", lazy="dynamic")
    reports_submitted = db.relationship("Report", foreign_keys="Report.reporter_id", back_populates="reporter", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initials(self):
        parts = self.display_name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        elif parts:
            return parts[0][:2].upper()
        return "SM"

    @property
    def college_name(self):
        if self.college_name_custom:
            return self.college_name_custom
        return self.college.name if self.college else "General Campus"

    @property
    def display_college(self):
        if self.college_name_custom:
            return self.college_name_custom
        if self.college:
            return self.college.short_name or self.college.name
        return "Campus Student"

    def unread_notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def __repr__(self):
        return f"<User {self.email}>"


class Listing(db.Model):
    """Marketplace product listing created by students."""
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), index=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Listing Type: "For Sale", "Free", "Lend/Borrow"
    listing_type = db.Column(db.String(30), default="For Sale", index=True)
    
    price = db.Column(db.Integer, nullable=False)  # in INR ₹ (0 if Free or peer lend)
    original_price = db.Column(db.Integer, nullable=True)  # Original purchase MRP in INR
    category = db.Column(db.String(60), index=True, nullable=False)
    condition = db.Column(db.String(30), nullable=False)  # New, Like New, Good, Fair, Needs Repair
    condition_notes = db.Column(db.Text, nullable=True)  # Flaws, scratches, handwritten notes, highlighting, missing parts
    status = db.Column(db.String(20), default="Available", index=True)  # Available, Reserved, Sold, Lent, Hidden
    moderation_status = db.Column(db.String(20), default="Approved", index=True)  # Approved, Flagged, Rejected
    is_demo_sample = db.Column(db.Boolean, default=False)  # Clearly flags sample demo records
    
    # Location fields
    state = db.Column(db.String(100), default="Gujarat", index=True)
    city = db.Column(db.String(100), default="Ahmedabad", index=True)
    pickup_area = db.Column(db.String(150), nullable=False)  # Campus meeting area
    
    # Lending / Borrowing specific terms
    lend_duration = db.Column(db.String(60), nullable=True)  # e.g., "1 week", "Semester-long", "Exam week"
    lend_deposit = db.Column(db.Integer, nullable=True)  # Refundable security deposit in INR
    lend_terms = db.Column(db.Text, nullable=True)  # Return expectations & conditions
    
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Foreign Keys
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey("colleges.id"), nullable=True)
    college_name_custom = db.Column(db.String(150), nullable=True)

    # Relationships
    seller = db.relationship("User", back_populates="listings")
    college = db.relationship("College", back_populates="listings")
    images = db.relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan", lazy="joined")
    orders = db.relationship("Order", back_populates="listing", lazy="dynamic")
    conversations = db.relationship("Conversation", back_populates="listing", lazy="dynamic")
    reports = db.relationship("Report", back_populates="listing", lazy="dynamic")

    @property
    def primary_image_url(self):
        for img in self.images:
            if img.is_primary:
                return img.image_path
        if self.images:
            return self.images[0].image_path
        return "img/placeholders/no-photo.svg"

    @property
    def category_placeholder_url(self):
        category_fallbacks = {
            "Scientific Calculators": "img/products/calculator.jpg",
            "Books & Study Notes": "img/products/maths-book.jpg",
            "Engineering Drawing & Tools": "img/products/drafter.jpg",
            "Lab Equipment & Coats": "img/products/lab-coat.jpg",
            "Electronics & Laptops": "img/products/arduino.jpg",
            "Hostel Essentials & Appliances": "img/products/kettle-lamp.jpg",
            "Cycles & Campus Mobility": "img/products/bicycle.jpg",
        }
        return category_fallbacks.get(self.category, "img/placeholders/no-photo.svg")

    @property
    def display_college(self):
        if self.college_name_custom:
            return self.college_name_custom
        if self.college:
            return self.college.short_name or self.college.name
        return f"{self.city} Campus"

    @property
    def college_display_name(self):
        if self.college_name_custom:
            return self.college_name_custom
        if self.college:
            return self.college.name
        return f"{self.city} Campus"

    @property
    def is_free(self):
        return self.listing_type == "Free" or self.price == 0

    @property
    def is_lend(self):
        return self.listing_type == "Lend/Borrow"

    @property
    def savings_percentage(self):
        if self.original_price and self.original_price > self.price and self.price > 0:
            savings = ((self.original_price - self.price) / self.original_price) * 100
            return int(round(savings))
        return None

    def __repr__(self):
        return f"<Listing {self.id}: {self.title[:30]}>"


class ListingImage(db.Model):
    """Image attachments for product listings."""
    __tablename__ = "listing_images"

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    listing = db.relationship("Listing", back_populates="images")


class UrgentRequest(db.Model):
    """Urgent Need requests posted by students with automatic expiration."""
    __tablename__ = "urgent_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey("colleges.id"), nullable=True)
    
    title = db.Column(db.String(160), index=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), index=True, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # Urgency tier: "Within 1 hour", "Today", "Tomorrow", "Flexible"
    urgency = db.Column(db.String(30), nullable=False)
    
    # Location
    state = db.Column(db.String(100), default="Gujarat", index=True, nullable=False)
    city = db.Column(db.String(100), default="Ahmedabad", index=True, nullable=False)
    college_name_custom = db.Column(db.String(150), nullable=True)
    
    budget = db.Column(db.Integer, nullable=True)  # Optional budget in INR
    preferred_pickup = db.Column(db.String(150), nullable=False)
    image_path = db.Column(db.String(255), nullable=True)  # Optional reference photo
    
    # Status: "Active", "Fulfilled", "Cancelled", "Expired"
    status = db.Column(db.String(20), default="Active", index=True)
    moderation_status = db.Column(db.String(20), default="Approved", index=True)
    is_demo_sample = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    # Relationships
    user = db.relationship("User", back_populates="urgent_requests")
    college = db.relationship("College")
    offers = db.relationship("UrgentOffer", back_populates="urgent_request", cascade="all, delete-orphan", order_by="UrgentOffer.created_at.desc()")
    reports = db.relationship("Report", back_populates="urgent_request", lazy="dynamic")

    @classmethod
    def calculate_expiry(cls, urgency_option, base_time=None):
        base = base_time or datetime.utcnow()
        if urgency_option == "Within 1 hour":
            return base + timedelta(hours=1)
        elif urgency_option == "Today":
            return base + timedelta(hours=6)
        elif urgency_option == "Tomorrow":
            return base + timedelta(hours=24)
        else:  # Flexible
            return base + timedelta(days=7)

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def effective_status(self):
        if self.status == "Active" and self.is_expired:
            return "Expired"
        return self.status

    @property
    def time_remaining_str(self):
        now = datetime.utcnow()
        if now >= self.expires_at:
            return "Expired"
        diff = self.expires_at - now
        total_seconds = int(diff.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 24:
            days = hours // 24
            return f"{days}d left"
        if hours > 0:
            return f"{hours}h {minutes}m left"
        return f"{minutes}m left"

    @property
    def display_college(self):
        if self.college:
            return self.college.short_name or self.college.name
        return self.college_name_custom or f"{self.city} Campus"

    def __repr__(self):
        return f"<UrgentRequest {self.id}: {self.title[:30]}>"


class UrgentOffer(db.Model):
    """Direct responses/offers submitted by other students to an urgent request."""
    __tablename__ = "urgent_offers"

    id = db.Column(db.Integer, primary_key=True)
    urgent_request_id = db.Column(db.Integer, db.ForeignKey("urgent_requests.id"), nullable=False)
    responder_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    message = db.Column(db.Text, nullable=False)
    price_offered = db.Column(db.Integer, nullable=True)  # In INR
    is_free_help = db.Column(db.Boolean, default=False)
    pickup_suggestion = db.Column(db.String(150), nullable=True)
    
    # Status: "Pending", "Accepted", "Declined"
    status = db.Column(db.String(20), default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    urgent_request = db.relationship("UrgentRequest", back_populates="offers")
    responder = db.relationship("User", back_populates="urgent_offers")


class Notification(db.Model):
    """In-app alert for user actions like urgent offers, orders, and messages."""
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(40), default="urgent")  # urgent, message, order, system
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship("User", back_populates="notifications")


class Conversation(db.Model):
    """Direct message thread between buyer and seller regarding a specific item."""
    __tablename__ = "conversations"
    __table_args__ = (
        db.UniqueConstraint("listing_id", "buyer_id", name="uq_listing_buyer_conversation"),
    )

    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    # Relationships
    listing = db.relationship("Listing", back_populates="conversations")
    buyer = db.relationship("User", foreign_keys=[buyer_id])
    seller = db.relationship("User", foreign_keys=[seller_id])
    messages = db.relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

    def unread_count_for_user(self, user_id):
        return Message.query.filter(
            Message.conversation_id == self.id,
            Message.sender_id != user_id,
            Message.is_read == False
        ).count()

    def last_message(self):
        return Message.query.filter_by(conversation_id=self.id).order_by(Message.created_at.desc()).first()


class Message(db.Model):
    """Individual message inside a buyer-seller conversation."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship("User")


class Order(db.Model):
    """Student marketplace order with escrow lifecycle."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(32), unique=True, index=True, nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)  # Total in INR
    
    # State machine: PENDING -> ACCEPTED -> COMPLETED, or CANCELLED, DISPUTED
    status = db.Column(db.String(20), default="PENDING", index=True, nullable=False)
    payment_method = db.Column(db.String(30), default="DEMO_ESCROW")  # DEMO_ESCROW, RAZORPAY_TEST, CAMPUS_CASH
    payment_status = db.Column(db.String(20), default="HELD_IN_ESCROW") # PENDING, HELD_IN_ESCROW, RELEASED, REFUNDED
    
    pickup_location = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    dispute_reason = db.Column(db.Text, nullable=True)
    dispute_resolution = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    listing = db.relationship("Listing", back_populates="orders")
    buyer = db.relationship("User", foreign_keys=[buyer_id], back_populates="orders_bought")
    seller = db.relationship("User", foreign_keys=[seller_id], back_populates="orders_sold")
    payment_record = db.relationship("PaymentRecord", back_populates="order", uselist=False, cascade="all, delete-orphan")

    def can_transition_to(self, new_state, actor_user_id):
        is_buyer = (actor_user_id == self.buyer_id)
        is_seller = (actor_user_id == self.seller_id)

        if new_state == "ACCEPTED":
            return is_seller and self.status == "PENDING"
        elif new_state == "COMPLETED":
            return is_buyer and self.status in ["PENDING", "ACCEPTED"]
        elif new_state == "CANCELLED":
            return (is_buyer or is_seller) and self.status in ["PENDING", "ACCEPTED"]
        elif new_state == "DISPUTED":
            return (is_buyer or is_seller) and self.status in ["PENDING", "ACCEPTED", "COMPLETED"]
        return False


class PaymentRecord(db.Model):
    """Payment record linked to an order."""
    __tablename__ = "payment_records"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    gateway = db.Column(db.String(40), default="CAMPUS_DEMO_ESCROW")  # CAMPUS_DEMO_ESCROW, RAZORPAY_TEST
    gateway_order_id = db.Column(db.String(100), nullable=True)
    gateway_payment_id = db.Column(db.String(100), nullable=True)
    gateway_signature = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), default="INR")
    status = db.Column(db.String(30), default="PAID")
    is_verified = db.Column(db.Boolean, default=False)
    verification_notes = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    order = db.relationship("Order", back_populates="payment_record")


class Report(db.Model):
    """Trust & safety report filed by students against a listing, urgent request, or user."""
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id"), nullable=True)
    urgent_request_id = db.Column(db.Integer, db.ForeignKey("urgent_requests.id"), nullable=True)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="PENDING", index=True)  # PENDING, REVIEWED, DISMISSED, ACTION_TAKEN
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    reporter = db.relationship("User", foreign_keys=[reporter_id], back_populates="reports_submitted")
    listing = db.relationship("Listing", back_populates="reports")
    urgent_request = db.relationship("UrgentRequest", back_populates="reports")
    reported_user = db.relationship("User", foreign_keys=[reported_user_id])


class ContactMessage(db.Model):
    """Contact inquiries submitted via Contact Us form."""
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    college = db.Column(db.String(150), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def ensure_schema_upgrades(engine):
    """
    Safely adds missing columns to existing SQLite database tables without dropping data.
    Runs during application startup. Gracefully skipped for non-SQLite databases where
    full schemas are created natively by SQLAlchemy.
    """
    if engine.dialect.name != "sqlite":
        return

    with engine.connect() as conn:
        # Check users table
        try:
            columns = [row[1] for row in conn.execute(text("PRAGMA table_info(users)")).fetchall()]
            if columns:
                if "is_email_verified" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_email_verified BOOLEAN DEFAULT 0"))
                if "is_google_authenticated" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_google_authenticated BOOLEAN DEFAULT 0"))
                if "preferred_state" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN preferred_state VARCHAR(100) DEFAULT 'Gujarat'"))
                if "preferred_city" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN preferred_city VARCHAR(100) DEFAULT 'Ahmedabad'"))
                if "college_name_custom" not in columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN college_name_custom VARCHAR(150)"))
                conn.commit()
        except Exception as e:
            print(f"[Schema Upgrade] users notice: {e}")

        # Check listings table
        try:
            columns = [row[1] for row in conn.execute(text("PRAGMA table_info(listings)")).fetchall()]
            if columns:
                if "listing_type" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN listing_type VARCHAR(30) DEFAULT 'For Sale'"))
                if "state" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN state VARCHAR(100) DEFAULT 'Gujarat'"))
                if "city" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN city VARCHAR(100) DEFAULT 'Ahmedabad'"))
                if "lend_duration" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN lend_duration VARCHAR(60)"))
                if "lend_deposit" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN lend_deposit INTEGER"))
                if "lend_terms" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN lend_terms TEXT"))
                if "college_name_custom" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN college_name_custom VARCHAR(150)"))
                if "condition_notes" not in columns:
                    conn.execute(text("ALTER TABLE listings ADD COLUMN condition_notes TEXT"))
                conn.commit()
        except Exception as e:
            print(f"[Schema Upgrade] listings notice: {e}")

        # Check reports table
        try:
            columns = [row[1] for row in conn.execute(text("PRAGMA table_info(reports)")).fetchall()]
            if columns:
                if "urgent_request_id" not in columns:
                    conn.execute(text("ALTER TABLE reports ADD COLUMN urgent_request_id INTEGER REFERENCES urgent_requests(id)"))
                conn.commit()
        except Exception as e:
            print(f"[Schema Upgrade] reports notice: {e}")
