function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;

    const chatBody = document.getElementById('chat-body');
    const isAtBottom = chatBody.scrollHeight - chatBody.scrollTop <= chatBody.clientHeight + 10; // Check if user is at bottom

    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'chat-message user-message';
    userMessageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <img src="/static/user-logo.svg" class="logo" alt="User Logo">
    `;
    chatBody.appendChild(userMessageDiv);

    // Only scroll if user is at the bottom
    if (isAtBottom) {
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    input.value = '';
    input.disabled = true;
    document.querySelector('.chat-input button').disabled = true;

    // Add typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.innerHTML = `
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
    `;
    chatBody.appendChild(typingIndicator);

    // Scroll to typing indicator if user is at the bottom
    if (isAtBottom) {
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        chatBody.removeChild(typingIndicator);

        const botMessageDiv = document.createElement('div');
        botMessageDiv.className = `chat-message bot-message`;
        botMessageDiv.innerHTML = `
            <img src="/static/chatbot-logo.svg" class="logo" alt="Assessly Logo">
            <div class="message-content">${data.response}</div>
        `;
        chatBody.appendChild(botMessageDiv);

        // Only scroll if user is at the bottom
        if (isAtBottom) {
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        input.disabled = false;
        document.querySelector('.chat-input button').disabled = false;
        input.focus();
    })
    .catch(error => {
        // Remove typing indicator
        chatBody.removeChild(typingIndicator);

        const errorMessageDiv = document.createElement('div');
        errorMessageDiv.className = 'chat-message bot-message';
        errorMessageDiv.innerHTML = `
            <img src="/static/chatbot-logo.svg" class="logo" alt="Assessly Logo">
            <div class="message-content">Sorry, something went wrong. Please try again.</div>
        `;
        chatBody.appendChild(errorMessageDiv);

        // Only scroll if user is at the bottom
        if (isAtBottom) {
            chatBody.scrollTop = chatBody.scrollHeight;
        }

        input.disabled = false;
        document.querySelector('.chat-input button').disabled = false;
        input.focus();
    });
}

function sendQuickReply(message) {
    const input = document.getElementById('user-input');
    input.value = message;
    sendMessage();
}

document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});