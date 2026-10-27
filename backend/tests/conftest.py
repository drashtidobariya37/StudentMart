import pytest
from app import create_app
from app.models import db, College, User, Listing, ListingImage, Conversation, Message, Order, PaymentRecord

@pytest.fixture
def app():
    """Creates a test application instance with in-memory SQLite database."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()

        # Seed minimal fixtures
        college = College(
            name="COEP Technological University",
            short_name="COEP",
            city="Pune",
            state="Maharashtra",
            domain="coeptech.ac.in",
            campus_zones="Central Library, Main Canteen"
        )
        db.session.add(college)
        db.session.flush()

        # Seed Seller
        seller = User(
            email="seller@coeptech.ac.in",
            display_name="Test Seller",
            college_id=college.id,
            is_verified_student=True,
            is_admin=False
        )
        seller.set_password("SellerPass123")
        db.session.add(seller)

        # Seed Buyer
        buyer = User(
            email="buyer@coeptech.ac.in",
            display_name="Test Buyer",
            college_id=college.id,
            is_verified_student=True,
            is_admin=False
        )
        buyer.set_password("BuyerPass123")
        db.session.add(buyer)

        # Seed Admin
        admin = User(
            email="admin@studentmart.campus",
            display_name="Admin User",
            college_id=college.id,
            is_verified_student=True,
            is_admin=True
        )
        admin.set_password("AdminPass123")
        db.session.add(admin)

        # Seed 3rd party outsider
        outsider = User(
            email="outsider@coeptech.ac.in",
            display_name="Outsider User",
            college_id=college.id,
            is_verified_student=False,
            is_admin=False
        )
        outsider.set_password("OutsiderPass123")
        db.session.add(outsider)
        db.session.flush()

        # Seed a test listing
        listing = Listing(
            title="B.S. Grewal Higher Engineering Mathematics",
            description="Clean condition 44th edition for semester 1 and 2 mathematics.",
            price=450,
            original_price=950,
            category="Books & Study Notes",
            condition="Good",
            pickup_area="Central Library Steps",
            status="Available",
            moderation_status="Approved",
            seller_id=seller.id,
            college_id=college.id
        )
        db.session.add(listing)
        db.session.flush()

        img = ListingImage(listing_id=listing.id, image_path="img/placeholders/book.svg", is_primary=True)
        db.session.add(img)

        db.session.commit()

        yield test_app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()

@pytest.fixture
def seller_client(app):
    """Client authenticated as seller."""
    c = app.test_client()
    with c.session_transaction() as sess:
        user = User.query.filter_by(email="seller@coeptech.ac.in").first()
        sess["user_id"] = user.id
        sess["user_display_name"] = user.display_name
        sess["user_is_admin"] = False
    return c

@pytest.fixture
def buyer_client(app):
    """Client authenticated as buyer."""
    c = app.test_client()
    with c.session_transaction() as sess:
        user = User.query.filter_by(email="buyer@coeptech.ac.in").first()
        sess["user_id"] = user.id
        sess["user_display_name"] = user.display_name
        sess["user_is_admin"] = False
    return c

@pytest.fixture
def outsider_client(app):
    """Client authenticated as third-party student."""
    c = app.test_client()
    with c.session_transaction() as sess:
        user = User.query.filter_by(email="outsider@coeptech.ac.in").first()
        sess["user_id"] = user.id
        sess["user_display_name"] = user.display_name
        sess["user_is_admin"] = False
    return c

@pytest.fixture
def admin_client(app):
    """Client authenticated as administrator."""
    c = app.test_client()
    with c.session_transaction() as sess:
        user = User.query.filter_by(email="admin@studentmart.campus").first()
        sess["user_id"] = user.id
        sess["user_display_name"] = user.display_name
        sess["user_is_admin"] = True
    return c
