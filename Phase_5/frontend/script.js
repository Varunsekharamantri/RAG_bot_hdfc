document.addEventListener('DOMContentLoaded', () => {
    const fab = document.getElementById('fab');
    const assistantWidget = document.getElementById('assistant-widget');
    const closeAssistant = document.getElementById('close-assistant');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');
    const chips = document.querySelectorAll('.chip');

    const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const API_URL = isLocal && window.location.port !== '8000' ? 'http://localhost:8000/chat' : '/chat';

    // Toggle widget
    fab.addEventListener('click', () => {
        assistantWidget.classList.toggle('hidden');
    });

    closeAssistant.addEventListener('click', () => {
        assistantWidget.classList.add('hidden');
    });

    // Handle chips
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chatInput.value = chip.textContent;
            sendMessage();
        });
    });

    // Handle Enter key
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Handle Send Button
    sendBtn.addEventListener('click', () => {
        sendMessage();
    });

    async function sendMessage() {
        const query = chatInput.value.trim();
        if (!query) return;

        // 1. Add user message to UI
        addMessage(query, 'user');
        chatInput.value = '';

        // 2. Add loading state
        const loadingId = 'loading-' + Date.now();
        addMessage('Thinking...', 'assistant', loadingId);

        // 3. Call API
        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query })
            });

            const data = await response.json();
            
            // Remove loading
            document.getElementById(loadingId).remove();

            // 4. Render response based on type
            if (data.type === 'refusal') {
                // Style as a styled note card
                const refusalHtml = `
                    <div class="message refusal">
                        <i class="fa-solid fa-triangle-exclamation warning-icon"></i>
                        ${data.text.replace(/\n/g, '<br>')}
                    </div>
                `;
                chatMessages.insertAdjacentHTML('beforeend', refusalHtml);
            } else if (data.type === 'error') {
                const errorHtml = `
                    <div class="message refusal">
                        <i class="fa-solid fa-circle-exclamation warning-icon" style="color: #d32f2f;"></i>
                        ${data.text}
                    </div>
                `;
                chatMessages.insertAdjacentHTML('beforeend', errorHtml);
            } else {
                // Factual (Normal assistant message)
                addMessage(data.text, 'assistant');
            }

            scrollToBottom();

        } catch (error) {
            console.error('API Error:', error);
            document.getElementById(loadingId).remove();
            addMessage('Could not connect to the server. Is the FastAPI backend running?', 'assistant');
            scrollToBottom();
        }
    }

    function addMessage(text, sender, id = null) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        if (id) msgDiv.id = id;
        
        // 1. Convert Markdown links [text](url) to HTML <a> tags
        let formattedText = text.replace(/\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank" style="color: var(--teal); font-weight: 500; text-decoration: none;">$1</a>');
        
        // 2. Convert remaining raw URLs to HTML <a> tags (excluding those already inside href="")
        formattedText = formattedText.replace(/(^|[^"'])(https?:\/\/[^\s]+)/g, '$1<a href="$2" target="_blank" style="color: var(--teal); font-weight: 500; text-decoration: none;">$2</a>');
        
        // 3. Convert newlines to breaks
        formattedText = formattedText.replace(/\n/g, '<br>');
        
        msgDiv.innerHTML = formattedText;
        
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
