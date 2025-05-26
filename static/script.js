<<<<<<< HEAD
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
=======
async function sendMessage() {
    const input = document.getElementById('user-input');
    const chatBody = document.getElementById('chat-body');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    const userMessage = document.createElement('div');
    userMessage.className = 'chat-message user-message animate__animated animate__slideInRight';
    userMessage.innerHTML = `
        <div class="message-content">${message}</div>
        <img src="/static/user-logo.svg?v=1" class="logo" alt="User Logo">
    `;
    chatBody.appendChild(userMessage);

    input.value = '';

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.className = 'typing-indicator';
    typingIndicator.style.display = 'block';
    chatBody.appendChild(typingIndicator);
    chatBody.scrollTop = chatBody.scrollHeight;

    // Try sending message with retry
    let response, data;
    for (let attempt = 0; attempt < 2; attempt++) {
        try {
            response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });
            data = await response.json();
            break;
        } catch (error) {
            if (attempt === 0) {
                await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2s before retry
                continue;
            }
            typingIndicator.remove();
            const errorMessage = document.createElement('div');
            errorMessage.className = 'chat-message bot-message error-message animate__animated animate__slideInLeft';
            errorMessage.innerHTML = `
                <img src="/static/chatbot-logo.svg?v=1" class="logo" alt="Assessly Logo">
                <div class="message-content">Network error. Please check your connection and try again.</div>
            `;
            chatBody.appendChild(errorMessage);
            chatBody.scrollTop = chatBody.scrollHeight;
            return;
        }
    }

    // Remove typing indicator
    typingIndicator.remove();

    // Add bot response
    const botMessage = document.createElement('div');
    botMessage.className = `chat-message bot-message animate__animated animate__slideInLeft ${data.response.includes('Sorry') || data.response.includes('Error') ? 'error-message' : ''}`;
    botMessage.innerHTML = `
        <img src="/static/chatbot-logo.svg?v=1" class="logo" alt="Assessly Logo">
        <div class="message-content">${data.response}</div>
    `;
    chatBody.appendChild(botMessage);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function sendQuickReply(message) {
    document.getElementById('user-input').value = message;
    sendMessage();
}

function toggleTheme() {
    document.documentElement.classList.toggle('dark');
    const toggle = document.querySelector('.theme-toggle');
    toggle.textContent = document.documentElement.classList.contains('dark') ? '☀️' : '🌙';
}

document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
>>>>>>> 5c8a5f949e056a57969828685d12992e5b50a717
});