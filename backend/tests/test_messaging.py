from app.models import Conversation, Message

def test_start_conversation_and_send_message(buyer_client):
    """Verify buyer can initiate a conversation regarding an item and send messages."""
    # Start chat with seller on listing 1
    response = buyer_client.get("/messages/start/1", follow_redirects=True)
    assert response.status_code == 200

    conv = Conversation.query.filter_by(listing_id=1).first()
    assert conv is not None

    # Post a message
    response2 = buyer_client.post(f"/messages/{conv.id}/send", data={
        "content": "Can you meet at the library portico tomorrow at 3 PM?"
    }, follow_redirects=True)
    assert response2.status_code == 200

    latest_msg = Message.query.filter_by(conversation_id=conv.id).order_by(Message.id.desc()).first()
    assert latest_msg is not None
    assert "library portico" in latest_msg.content

def test_messaging_privacy_enforcement(buyer_client, outsider_client):
    """Verify private messages are strictly restricted to participants (403 for outsiders)."""
    # Create conversation between Buyer and Seller
    buyer_client.get("/messages/start/1", follow_redirects=True)
    conv = Conversation.query.filter_by(listing_id=1).first()
    assert conv is not None

    # Outsider attempts to view conversation
    response = outsider_client.get(f"/messages/{conv.id}")
    assert response.status_code == 403

    # Outsider attempts to send a message into the thread
    response_post = outsider_client.post(f"/messages/{conv.id}/send", data={
        "content": "Sneaking into private chat"
    })
    assert response_post.status_code == 403
