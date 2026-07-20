<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>AI Chat Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .message-animate {
            animation: fadeIn 0.3s ease-out;
        }
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #94a3b8;
            margin: 0 2px;
            animation: typing 1.4s infinite both;
        }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing {
            0% { opacity: 0.2; transform: scale(0.8); }
            50% { opacity: 1; transform: scale(1.2); }
            100% { opacity: 0.2; transform: scale(0.8); }
        }
        .chat-container {
            height: calc(100vh - 200px);
            overflow-y: auto;
            scroll-behavior: smooth;
        }
        .chat-container::-webkit-scrollbar {
            width: 6px;
        }
        .chat-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }
        .chat-container::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        .chat-container::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div class="max-w-4xl mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-t-xl shadow-sm border border-gray-200 p-4 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    <i class="fas fa-robot text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-lg font-semibold text-gray-800">AI Assistant</h1>
                    <p class="text-xs text-gray-500">Powered by Groq • Llama 3.1</p>
                </div>
            </div>
            <button onclick="clearChat()" class="text-gray-400 hover:text-red-500 transition">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>

        <!-- Chat Messages -->
        <div id="chatContainer" class="chat-container bg-gray-50 border-x border-gray-200 p-4 space-y-4">
            <!-- Welcome Message -->
            <div class="text-center text-gray-400 text-sm py-8">
                <i class="fas fa-comment-dots text-3xl block mb-3 text-gray-300"></i>
                <p>Start a conversation with the AI assistant</p>
                <p class="text-xs mt-1">Ask me anything!</p>
            </div>
        </div>

        <!-- Input Area -->
        <div class="bg-white rounded-b-xl shadow-sm border border-gray-200 p-4">
            <form id="chatForm" class="flex space-x-3">
                @csrf
                <div class="flex-1 relative">
                    <input
                        type="text"
                        id="messageInput"
                        name="message"
                        placeholder="Type your message here..."
                        class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition pr-12"
                        autocomplete="off"
                        required
                    >
                    <button
                        type="submit"
                        id="sendButton"
                        class="absolute right-2 top-1/2 -translate-y-1/2 text-blue-500 hover:text-blue-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <i class="fas fa-paper-plane text-lg"></i>
                    </button>
                </div>
                <button
                    type="button"
                    onclick="clearChat()"
                    class="px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-lg transition text-gray-600"
                >
                    <i class="fas fa-eraser"></i>
                </button>
            </form>
            <div class="mt-2 text-xs text-gray-400 text-center">
                <span id="charCount">0</span> / 1000 characters
            </div>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const chatForm = document.getElementById('chatForm');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const charCount = document.getElementById('charCount');

        // Character counter
        messageInput.addEventListener('input', function() {
            charCount.textContent = this.value.length;
        });

        // Submit message
        chatForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const message = messageInput.value.trim();
            if (!message) return;

            // Add user message to chat
            addMessage('user', message);

            // Clear input
            messageInput.value = '';
            charCount.textContent = '0';

            // Show typing indicator
            const typingId = showTypingIndicator();

            // Disable send button
            sendButton.disabled = true;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify({ message })
                });

                const data = await response.json();

                // Remove typing indicator
                removeTypingIndicator(typingId);

                if (data.success) {
                    addMessage('assistant', data.reply);
                } else {
                    addMessage('error', data.error || 'Something went wrong. Please try again.');
                }
            } catch (error) {
                removeTypingIndicator(typingId);
                addMessage('error', 'Network error. Please check your connection.');
                console.error('Chat error:', error);
            } finally {
                sendButton.disabled = false;
            }
        });

        // Add message to chat
        function addMessage(role, content) {
            const welcomeDiv = chatContainer.querySelector('.text-center');
            if (welcomeDiv) welcomeDiv.remove();

            const messageDiv = document.createElement('div');
            messageDiv.className = `flex items-start space-x-3 message-animate ${role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`;

            const avatar = document.createElement('div');
            avatar.className = `flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                role === 'user' ? 'bg-purple-500' :
                role === 'error' ? 'bg-red-500' : 'bg-blue-500'
            }`;
            avatar.innerHTML = role === 'user' ? '<i class="fas fa-user text-white text-sm"></i>' :
                              role === 'error' ? '<i class="fas fa-exclamation-triangle text-white text-sm"></i>' :
                              '<i class="fas fa-robot text-white text-sm"></i>';

            const contentDiv = document.createElement('div');
            contentDiv.className = `max-w-[80%] px-4 py-3 rounded-2xl ${
                role === 'user' ? 'bg-purple-500 text-white rounded-tr-none' :
                role === 'error' ? 'bg-red-100 text-red-800 border border-red-200 rounded-tl-none' :
                'bg-white text-gray-800 border border-gray-200 rounded-tl-none'
            }`;
            contentDiv.innerHTML = formatMessage(content);

            messageDiv.appendChild(avatar);
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);

            scrollToBottom();
        }

        // Format message (basic markdown-like formatting)
        function formatMessage(text) {
            // Handle code blocks
            text = text.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre class="bg-gray-800 text-white p-3 rounded-lg overflow-x-auto my-2 text-sm"><code>${escapeHtml(code.trim())}</code></pre>`;
            });

            // Handle inline code
            text = text.replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>');

            // Handle bold
            text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

            // Handle italic
            text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

            // Handle line breaks
            text = text.replace(/\n/g, '<br>');

            return text;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Typing indicator
        function showTypingIndicator() {
            const id = 'typing-' + Date.now();
            const div = document.createElement('div');
            div.id = id;
            div.className = 'flex items-start space-x-3 message-animate';
            div.innerHTML = `
                <div class="flex-shrink-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <i class="fas fa-robot text-white text-sm"></i>
                </div>
                <div class="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-tl-none">
                    <div class="typing-indicator flex space-x-1">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            chatContainer.appendChild(div);
            scrollToBottom();
            return id;
        }

        function removeTypingIndicator(id) {
            const element = document.getElementById(id);
            if (element) element.remove();
        }

        // Clear chat
        async function clearChat() {
            if (!confirm('Clear all messages?')) return;

            try {
                const response = await fetch('/chat/clear', {
                    method: 'DELETE',
                    headers: {
                        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').content
                    }
                });

                const data = await response.json();
                if (data.success) {
                    chatContainer.innerHTML = `
                        <div class="text-center text-gray-400 text-sm py-8">
                            <i class="fas fa-comment-dots text-3xl block mb-3 text-gray-300"></i>
                            <p>Chat history cleared</p>
                            <p class="text-xs mt-1">Start a new conversation</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error clearing chat:', error);
            }
        }

        // Scroll to bottom
        function scrollToBottom() {
            setTimeout(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }, 100);
        }

        // Enter key to submit
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });

        // Initial scroll to bottom
        scrollToBottom();
    </script>
</body>
</html>
