from app.models import Order, Listing

def test_order_placement_demo_escrow(buyer_client):
    """Verify buyer can place an order via Campus Safe Demo Escrow."""
    response = buyer_client.post("/orders/checkout/1", data={
        "payment_method": "DEMO_ESCROW",
        "pickup_location": "Central Library Steps",
        "notes": "Will arrive at 2 PM sharp."
    }, follow_redirects=True)

    assert response.status_code == 200
    order = Order.query.filter_by(listing_id=1).first()
    assert order is not None
    assert order.status == "PENDING"
    assert order.payment_status == "HELD_IN_ESCROW"
    assert order.listing.status == "Reserved"

def test_seller_cannot_purchase_own_item(seller_client):
    """Verify seller is prohibited from purchasing their own listing."""
    response = seller_client.get("/orders/checkout/1", follow_redirects=True)
    assert response.status_code == 200
    assert b"You cannot purchase your own listing" in response.data

def test_order_lifecycle_state_transitions(buyer_client, seller_client, outsider_client):
    """Verify the strict order state transition lifecycle."""
    # 1. Buyer places order
    buyer_client.post("/orders/checkout/1", data={
        "payment_method": "DEMO_ESCROW",
        "pickup_location": "Central Library"
    }, follow_redirects=True)

    order = Order.query.filter_by(listing_id=1).first()
    assert order.status == "PENDING"

    # 2. Unauthorized attempt: Buyer tries to accept their own order (Only seller can accept)
    resp_unauth = buyer_client.post(f"/orders/{order.id}/action", data={"action": "ACCEPTED"}, follow_redirects=True)
    assert b"You are not authorized" in resp_unauth.data
    order = Order.query.get(order.id)
    assert order.status == "PENDING"

    # 3. Seller accepts order
    seller_client.post(f"/orders/{order.id}/action", data={"action": "ACCEPTED"}, follow_redirects=True)
    order = Order.query.get(order.id)
    assert order.status == "ACCEPTED"

    # 4. Buyer completes order after campus handoff
    buyer_client.post(f"/orders/{order.id}/action", data={"action": "COMPLETED"}, follow_redirects=True)
    order = Order.query.get(order.id)
    assert order.status == "COMPLETED"
    assert order.payment_status == "RELEASED_TO_SELLER"
    assert order.listing.status == "Sold"

def test_order_dispute_submission(buyer_client):
    """Verify buyer can raise a formal dispute on an order."""
    buyer_client.post("/orders/checkout/1", data={"payment_method": "DEMO_ESCROW"}, follow_redirects=True)
    order = Order.query.filter_by(listing_id=1).first()

    response = buyer_client.post(f"/orders/{order.id}/dispute", data={
        "dispute_reason": "Item has multiple pages missing in Chapter 4."
    }, follow_redirects=True)

    assert response.status_code == 200
    order = Order.query.get(order.id)
    assert order.status == "DISPUTED"
    assert "Chapter 4" in order.dispute_reason
