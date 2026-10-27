from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, jsonify
from app.models import db, Conversation, Message, Listing, User, Report
from app.utils.auth import login_required, get_current_user

messages_bp = Blueprint("messages", __name__)

@messages_bp.route("/messages")
@login_required
def inbox():
    """List all private conversations for the logged-in student."""
    user = get_current_user()
    
    conversations = Conversation.query.filter(
        (Conversation.buyer_id == user.id) | (Conversation.seller_id == user.id)
    ).order_by(Conversation.updated_at.desc()).all()

    return render_template("messages/inbox.html", conversations=conversations, current_user=user)

@messages_bp.route("/messages/start/<int:listing_id>")
@login_required
def start_chat(listing_id):
    """Initiates or resumes a chat with the seller of a listing."""
    listing = Listing.query.get_or_404(listing_id)
    user = get_current_user()

    if listing.seller_id == user.id:
        flash("You cannot initiate a chat with yourself for your own item.", "warning")
        return redirect(url_for("listings.detail", listing_id=listing_id))

    # Look for existing conversation between this buyer and seller on this item
    conv = Conversation.query.filter_by(
        listing_id=listing.id,
        buyer_id=user.id,
        seller_id=listing.seller_id
    ).first()

    if not conv:
        conv = Conversation(
            listing_id=listing.id,
            buyer_id=user.id,
            seller_id=listing.seller_id
        )
        db.session.add(conv)
        db.session.commit()

        # Add initial greeting message
        greeting = Message(
            conversation_id=conv.id,
            sender_id=user.id,
            content=f"Hi {listing.seller.display_name}, I am interested in your listing '{listing.title}'. Is it still available for campus pickup?"
        )
        db.session.add(greeting)
        db.session.commit()

    return redirect(url_for("messages.view", conversation_id=conv.id))

@messages_bp.route("/messages/<int:conversation_id>")
@login_required
def view(conversation_id):
    """View private conversation history and send replies."""
    conv = Conversation.query.get_or_404(conversation_id)
    user = get_current_user()

    # Access check: strictly restricted to buyer or seller (or admin)
    if user.id not in (conv.buyer_id, conv.seller_id) and not user.is_admin:
        abort(403)

    # Mark incoming unread messages as read
    Message.query.filter(
        Message.conversation_id == conv.id,
        Message.sender_id != user.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.session.commit()

    other_user = conv.seller if user.id == conv.buyer_id else conv.buyer

    # List of all conversations for sidebar navigation
    all_conversations = Conversation.query.filter(
        (Conversation.buyer_id == user.id) | (Conversation.seller_id == user.id)
    ).order_by(Conversation.updated_at.desc()).all()

    return render_template(
        "messages/conversation.html",
        conversation=conv,
        other_user=other_user,
        all_conversations=all_conversations,
        current_user=user
    )

@messages_bp.route("/messages/<int:conversation_id>/send", methods=["POST"])
@login_required
def send_message(conversation_id):
    """Post a new message to the conversation."""
    conv = Conversation.query.get_or_404(conversation_id)
    user = get_current_user()

    if user.id not in (conv.buyer_id, conv.seller_id) and not user.is_admin:
        abort(403)

    content = request.form.get("content", "").strip()
    if not content:
        flash("Message content cannot be blank.", "warning")
        return redirect(url_for("messages.view", conversation_id=conv.id))

    msg = Message(
        conversation_id=conv.id,
        sender_id=user.id,
        content=content,
        is_read=False
    )
    conv.updated_at = db.func.now()
    db.session.add(msg)
    db.session.commit()

    # If AJAX request, return JSON
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({
            "status": "success",
            "message": {
                "id": msg.id,
                "sender_id": msg.sender_id,
                "content": msg.content,
                "created_at": msg.created_at.strftime("%I:%M %p"),
                "is_me": True
            }
        })

    return redirect(url_for("messages.view", conversation_id=conv.id))

@messages_bp.route("/messages/<int:conversation_id>/api")
@login_required
def get_messages_api(conversation_id):
    """JSON API for real-time chat polling."""
    conv = Conversation.query.get_or_404(conversation_id)
    user = get_current_user()

    if user.id not in (conv.buyer_id, conv.seller_id) and not user.is_admin:
        abort(403)

    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at.asc()).all()
    
    # Mark messages as read
    Message.query.filter(
        Message.conversation_id == conv.id,
        Message.sender_id != user.id,
        Message.is_read == False
    ).update({"is_read": True})
    db.session.commit()

    return jsonify({
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": m.sender.display_name,
                "content": m.content,
                "created_at": m.created_at.strftime("%b %d, %I:%M %p"),
                "is_me": (m.sender_id == user.id)
            }
            for m in messages
        ]
    })

@messages_bp.route("/messages/<int:conversation_id>/report", methods=["POST"])
@login_required
def report_conversation(conversation_id):
    """Report inappropriate or abusive conduct in a conversation."""
    conv = Conversation.query.get_or_404(conversation_id)
    user = get_current_user()

    if user.id not in (conv.buyer_id, conv.seller_id):
        abort(403)

    other_user_id = conv.seller_id if user.id == conv.buyer_id else conv.buyer_id
    reason = request.form.get("reason", "Harassment / Inappropriate Behavior")
    details = request.form.get("details", "").strip()

    if not details:
        flash("Please explain the concern for the moderation team.", "warning")
        return redirect(url_for("messages.view", conversation_id=conv.id))

    report = Report(
        reporter_id=user.id,
        listing_id=conv.listing_id,
        reported_user_id=other_user_id,
        reason=reason,
        details=f"[From Message Thread #{conv.id}]: {details}",
        status="PENDING"
    )
    db.session.add(report)
    db.session.commit()

    flash("User report recorded. Our moderation team has been notified.", "info")
    return redirect(url_for("messages.view", conversation_id=conv.id))
