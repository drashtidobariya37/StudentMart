import pytest
from datetime import datetime, timedelta
from app.models import db, UrgentRequest, UrgentOffer, Notification, Listing, User

def test_urgent_feed_access(client):
    """Test that public urgent need feed renders correctly."""
    response = client.get("/urgent")
    assert response.status_code == 200
    assert b"Campus Urgent Needs Feed" in response.data
    assert b"Gujarat Hubs:" in response.data

def test_create_urgent_request(client, app):
    """Test creating a new urgent request as an authenticated student."""
    # Log in as seller
    client.post("/login", data={
        "email": "seller@coeptech.ac.in",
        "password": "SellerPass123"
    })

    response = client.post("/urgent/create", data={
        "title": "Need Casio 991EX for 11 AM exam today",
        "description": "Urgent practical exam requirement in computer lab. Need for 2 hours.",
        "category": "Scientific Calculators",
        "quantity": "1",
        "urgency": "Within 1 hour",
        "state": "Gujarat",
        "city": "Ahmedabad",
        "preferred_pickup": "Central Library entrance",
        "budget": "100"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Your urgent need request has been posted" in response.data

    with app.app_context():
        req = UrgentRequest.query.filter_by(title="Need Casio 991EX for 11 AM exam today").first()
        assert req is not None
        assert req.urgency == "Within 1 hour"
        assert req.city == "Ahmedabad"
        assert req.expires_at > datetime.utcnow()

def test_urgent_expiry_calculations():
    """Verify that UrgentRequest.calculate_expiry calculates appropriate deadlines."""
    now = datetime.utcnow()
    exp_1h = UrgentRequest.calculate_expiry("Within 1 hour", base_time=now)
    assert (exp_1h - now).total_seconds() <= 3605
    assert (exp_1h - now).total_seconds() >= 3595

    exp_today = UrgentRequest.calculate_expiry("Today", base_time=now)
    assert (exp_today - now).total_seconds() <= 21605

    exp_tomorrow = UrgentRequest.calculate_expiry("Tomorrow", base_time=now)
    assert (exp_tomorrow - now).total_seconds() <= 86405

def test_urgent_offer_and_accept_workflow(client, app):
    """Test full student help response and offer acceptance workflow."""
    with app.app_context():
        seller = User.query.filter_by(email="seller@coeptech.ac.in").first()
        buyer = User.query.filter_by(email="buyer@coeptech.ac.in").first()
        seller_id = seller.id

        req = UrgentRequest(
            user_id=seller.id,
            title="Need DBMS Notes urgently for tomorrow",
            description="Looking for clean handwritten transaction processing notes.",
            category="Books & Study Notes",
            urgency="Tomorrow",
            state="Gujarat",
            city="Gandhinagar",
            preferred_pickup="Resource Centre Lawn",
            status="Active",
            moderation_status="Approved",
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    # 1. Log in as Buyer to submit an offer
    client.post("/login", data={"email": "buyer@coeptech.ac.in", "password": "BuyerPass123"})
    offer_resp = client.post(f"/urgent/{req_id}/offer", data={
        "message": "I have the DBMS notes and can lend them at the Resource Centre!",
        "price_offered": "0",
        "is_free_help": "1",
        "pickup_suggestion": "Resource Centre Lawn"
    }, follow_redirects=True)
    assert offer_resp.status_code == 200
    assert b"Your offer has been submitted" in offer_resp.data

    with app.app_context():
        offer = UrgentOffer.query.filter_by(urgent_request_id=req_id).first()
        assert offer is not None
        assert offer.is_free_help is True
        offer_id = offer.id

        # Verify notification was sent to seller
        notif = Notification.query.filter_by(user_id=seller_id).first()
        assert notif is not None
        assert "New Offer" in notif.title

    # 2. Log out Buyer and log in as Seller (owner) to accept offer
    client.get("/logout")
    client.post("/login", data={"email": "seller@coeptech.ac.in", "password": "SellerPass123"})
    accept_resp = client.post(f"/urgent/{req_id}/accept-offer/{offer_id}", follow_redirects=True)
    assert accept_resp.status_code == 200
    assert b"marked as Fulfilled" in accept_resp.data

    with app.app_context():
        updated_req = db.session.get(UrgentRequest, req_id)
        updated_offer = db.session.get(UrgentOffer, offer_id)
        assert updated_req.status == "Fulfilled"
        assert updated_offer.status == "Accepted"

def test_owner_cannot_offer_on_own_request(client, app):
    """Test that a student cannot submit a help offer on their own request."""
    with app.app_context():
        seller = User.query.filter_by(email="seller@coeptech.ac.in").first()
        req = UrgentRequest(
            user_id=seller.id,
            title="Need mini drafter",
            description="Engineering drawing class test today.",
            category="Engineering Drawing & Tools",
            urgency="Today",
            state="Gujarat",
            city="Ahmedabad",
            preferred_pickup="Admin block",
            status="Active",
            moderation_status="Approved",
            expires_at=datetime.utcnow() + timedelta(hours=6)
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    client.post("/login", data={"email": "seller@coeptech.ac.in", "password": "SellerPass123"})
    resp = client.post(f"/urgent/{req_id}/offer", data={
        "message": "Self offering test",
        "price_offered": "50"
    }, follow_redirects=True)
    assert b"cannot submit an offer on your own urgent request" in resp.data

def test_set_location(client):
    """Test switching browsing location to Ahmedabad, Gujarat."""
    resp = client.post("/set-location", data={
        "state": "Gujarat",
        "city": "Ahmedabad"
    }, follow_redirects=True)
    assert resp.status_code == 200

    # Test JSON mode
    resp_json = client.post("/set-location", json={
        "state": "Gujarat",
        "city": "Gandhinagar"
    })
    assert resp_json.status_code == 200
    assert resp_json.json["success"] is True

def test_create_listing_with_lending_mode(client, app):
    """Test creating a listing with Lend/Borrow exchange mode."""
    client.post("/login", data={"email": "seller@coeptech.ac.in", "password": "SellerPass123"})

    response = client.post("/sell", data={
        "title": "Casio fx-991EX for Semester Exam Borrowing",
        "description": "Available for peer lending for upcoming semester exams. Please return with cover.",
        "category": "Scientific Calculators",
        "condition": "Like New",
        "listing_type": "Lend/Borrow",
        "price": "50",
        "lend_duration": "1 week",
        "lend_deposit": "500",
        "lend_terms": "Deposit refunded upon intact return.",
        "state": "Gujarat",
        "city": "Ahmedabad",
        "pickup_area": "Library porch",
        "college_id": "1"
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        listing = Listing.query.filter_by(title="Casio fx-991EX for Semester Exam Borrowing").first()
        assert listing is not None
        assert listing.listing_type == "Lend/Borrow"
        assert listing.lend_duration == "1 week"
        assert listing.lend_deposit == 500
        assert listing.city == "Ahmedabad"

def test_admin_urgent_moderation(client, app):
    """Test that an administrator can moderate urgent requests."""
    with app.app_context():
        seller = User.query.filter_by(email="seller@coeptech.ac.in").first()
        req = UrgentRequest(
            user_id=seller.id,
            title="Suspicious request needing moderation check",
            description="Testing admin moderation flagging.",
            category="Other",
            urgency="Flexible",
            state="Gujarat",
            city="Ahmedabad",
            preferred_pickup="Campus Gate",
            status="Active",
            moderation_status="Approved",
            expires_at=datetime.utcnow() + timedelta(days=2)
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    # Log in as Admin
    client.post("/login", data={"email": "admin@studentmart.campus", "password": "AdminPass123"})

    # Check urgent moderation queue
    resp = client.get("/admin/urgent")
    assert resp.status_code == 200
    assert b"Urgent Need Moderation Queue" in resp.data

    # Moderate to Flagged
    mod_resp = client.post(f"/admin/urgent/{req_id}/moderate", data={
        "action": "Flagged"
    }, follow_redirects=True)
    assert mod_resp.status_code == 200

    with app.app_context():
        updated = db.session.get(UrgentRequest, req_id)
        assert updated.moderation_status == "Flagged"
