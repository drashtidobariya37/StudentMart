/**
 * Student Mart - Interactive Buyer-Seller Messaging
 * Handles auto-scroll, message polling, and AJAX sending
 */

document.addEventListener("DOMContentLoaded", () => {
  const chatMessagesContainer = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");

  if (!chatMessagesContainer) return;

  // Auto-scroll to latest message
  function scrollToBottom() {
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  }
  scrollToBottom();

  const conversationId = chatMessagesContainer.getAttribute("data-conversation-id");
  if (!conversationId) return;

  // Real-time polling for new messages every 3.5 seconds
  let pollInterval = setInterval(fetchNewMessages, 3500);

  async function fetchNewMessages() {
    try {
      const response = await fetch(`/messages/${conversationId}/api`);
      if (!response.ok) return;
      const data = await response.json();
      
      if (data && data.messages) {
        const existingCount = chatMessagesContainer.querySelectorAll(".message-bubble").length;
        if (data.messages.length > existingCount) {
          // Render full list if new messages detected
          renderMessages(data.messages);
          scrollToBottom();
        }
      }
    } catch (err) {
      console.warn("Polling notice:", err);
    }
  }

  function renderMessages(messages) {
    chatMessagesContainer.innerHTML = "";
    messages.forEach((msg) => {
      const bubble = document.createElement("div");
      bubble.className = `message-bubble ${msg.is_me ? "message-mine" : "message-theirs"}`;
      bubble.innerHTML = `
        <div class="message-content">${escapeHtml(msg.content)}</div>
        <div class="message-time">${msg.created_at}</div>
      `;
      chatMessagesContainer.appendChild(bubble);
    });
  }

  // Handle AJAX message submit
  if (chatForm && messageInput) {
    chatForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const content = messageInput.value.trim();
      if (!content) return;

      const formData = new FormData(chatForm);
      messageInput.value = "";
      messageInput.focus();

      try {
        const res = await fetch(`/messages/${conversationId}/send`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-Token": getCsrfToken()
          },
          body: formData
        });

        if (res.ok) {
          fetchNewMessages();
        } else {
          // Fallback to standard submit if AJAX rejected
          chatForm.submit();
        }
      } catch (error) {
        chatForm.submit();
      }
    });
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.innerText = text;
    return div.innerHTML;
  }
});
