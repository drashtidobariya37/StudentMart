import hmac
import hashlib
from app.utils.payment import verify_razorpay_signature, process_demo_escrow_payment
from app.models import Order, PaymentRecord

def test_razorpay_signature_verification(app):
    """Verify HMAC-SHA256 signature verification logic."""
    with app.app_context():
        # Set a test secret
        app.config["RAZORPAY_KEY_SECRET"] = "secret_test_key_12345"

        order_id = "order_EKwxwAgItmmXdp"
        payment_id = "pay_29QQoUBi66xm2f"
        message = f"{order_id}|{payment_id}".encode("utf-8")
        valid_signature = hmac.new(b"secret_test_key_12345", message, hashlib.sha256).hexdigest()

        # Valid signature must pass
        assert verify_razorpay_signature(order_id, payment_id, valid_signature) is True

        # Tampered signature must fail
        tampered_signature = valid_signature[:-4] + "0000"
        assert verify_razorpay_signature(order_id, payment_id, tampered_signature) is False

def test_demo_escrow_payment_processing(app, buyer_client):
    """Verify demo escrow creates verified payment records and sets escrow holding."""
    buyer_client.post("/orders/checkout/1", data={"payment_method": "DEMO_ESCROW"}, follow_redirects=True)
    order = Order.query.filter_by(listing_id=1).first()

    assert order.payment_record is not None
    assert order.payment_record.gateway == "CAMPUS_DEMO_ESCROW"
    assert order.payment_record.is_verified is True
    assert order.payment_record.amount == order.amount
    assert order.payment_status == "HELD_IN_ESCROW"

def test_admin_dispute_resolution(buyer_client, admin_client):
    """Verify administrator can arbitrate an order dispute."""
    # Place order and raise dispute
    buyer_client.post("/orders/checkout/1", data={"payment_method": "DEMO_ESCROW"}, follow_redirects=True)
    order = Order.query.filter_by(listing_id=1).first()
    buyer_client.post(f"/orders/{order.id}/dispute", data={"dispute_reason": "Defective item."}, follow_redirects=True)

    # Admin resolves dispute in favor of Buyer (Refund)
    response = admin_client.post(f"/admin/orders/{order.id}/resolve_dispute", data={
        "resolution": "REFUND_BUYER",
        "resolution_notes": "Seller confirmed flaw. Refund processed."
    }, follow_redirects=True)

    assert response.status_code == 200
    order = Order.query.get(order.id)
    assert order.status == "CANCELLED"
    assert order.payment_status == "REFUNDED"
    assert order.listing.status == "Available"
