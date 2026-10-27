import hmac
import hashlib
import uuid
from flask import current_app
from app.models import db, Order, PaymentRecord

def is_razorpay_configured() -> bool:
    """Checks whether valid Razorpay test keys are provided in the environment."""
    key_id = current_app.config.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = current_app.config.get("RAZORPAY_KEY_SECRET", "").strip()
    
    # Check for placeholder or blank values
    if not key_id or not key_secret:
        return False
    if "your_key" in key_id.lower() or "your_secret" in key_secret.lower():
        return False
    return True

def create_razorpay_order(order: Order):
    """
    Creates an order on Razorpay using official SDK if configured.
    Amount is converted to paise (INR * 100).
    """
    if not is_razorpay_configured():
        return None

    try:
        import razorpay
        client = razorpay.Client(auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"]
        ))
        
        # Razorpay expects amount in paise (1 INR = 100 paise)
        amount_in_paise = int(order.amount * 100)
        data = {
            "amount": amount_in_paise,
            "currency": current_app.config.get("RAZORPAY_CURRENCY", "INR"),
            "receipt": order.order_number,
            "notes": {
                "listing_id": str(order.listing_id),
                "buyer_id": str(order.buyer_id),
                "seller_id": str(order.seller_id),
                "environment": "TEST_MODE"
            }
        }
        rp_order = client.order.create(data=data)
        return rp_order
    except Exception as e:
        current_app.logger.error(f"Failed to create Razorpay order: {e}")
        return None

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verifies Razorpay HMAC-SHA256 signature on server side.
    Payload = f"{order_id}|{payment_id}"
    """
    secret = current_app.config.get("RAZORPAY_KEY_SECRET", "").strip().encode("utf-8")
    if not secret:
        return False

    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected_signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_signature, signature)

def process_demo_escrow_payment(order: Order) -> PaymentRecord:
    """
    Processes a simulated Campus Safe Demo Escrow checkout.
    Clearly marks the payment as DEMO_ESCROW with verified test parameters.
    """
    demo_order_id = f"demo_order_{uuid.uuid4().hex[:12]}"
    demo_payment_id = f"demo_pay_{uuid.uuid4().hex[:12]}"
    demo_sig = hmac.new(b"demo_secret_2026", f"{demo_order_id}|{demo_payment_id}".encode(), hashlib.sha256).hexdigest()

    payment_record = PaymentRecord(
        order_id=order.id,
        gateway="CAMPUS_DEMO_ESCROW",
        gateway_order_id=demo_order_id,
        gateway_payment_id=demo_payment_id,
        gateway_signature=demo_sig,
        amount=order.amount,
        currency="INR",
        status="HELD_IN_ESCROW",
        is_verified=True,
        verification_notes="Simulated Student Campus Safe Escrow hold for demonstration."
    )
    
    order.status = "PENDING"
    order.payment_status = "HELD_IN_ESCROW"
    order.payment_method = "DEMO_ESCROW"
    
    db.session.add(payment_record)
    db.session.commit()
    return payment_record

def get_payment_disclaimer():
    """Returns official student marketplace disclaimer regarding direct peer-to-peer transfers."""
    return (
        "IMPORTANT NOTICE: Direct peer-to-peer UPI or QR transfers (such as Google Pay, PhonePe, or Paytm) "
        "are direct transfers between students. They do NOT provide automatic buyer escrow, delivery inspection, "
        "or dispute refund protection. Always meet in daylight at a designated campus safety spot before releasing payment."
    )
