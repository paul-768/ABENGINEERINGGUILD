// app/static/js/messages-fixed.js - COMPLETE FIXED VERSION
class FixedMessenger {
    constructor() {
        this.socket = null;
        this.currentConversationId = null;
        this.currentUserId = null;
        this.otherUserId = null;
        this.isTyping = false;
        this.typingTimeout = null;
        
        this.init();
    }

    init() {
        console.log('Initializing Fixed Messenger...');
        
        // Get conversation data from HTML
        this.extractConversationData();
        
        this.bindEvents();
        this.initializeSocketIO();
        this.loadMessages();
    }

    extractConversationData() {
        // Try multiple ways to get conversation data
        const conversationMeta = document.getElementById('conversationMeta');
        if (conversationMeta) {
            this.currentConversationId = conversationMeta.dataset.conversationId;
            this.currentUserId = conversationMeta.dataset.currentUserId;
            this.otherUserId = conversationMeta.dataset.otherUserId;
        } else {
            // Fallback: extract from URL or global variables
            const urlParts = window.location.pathname.split('/');
            const convId = urlParts[urlParts.length - 1];
            if (convId && !isNaN(convId)) {
                this.currentConversationId = parseInt(convId);
            }
            
            // Try to get user IDs from global scope
            if (typeof currentUserId !== 'undefined') {
                this.currentUserId = currentUserId;
            }
            
            // Extract other user ID from page content
            const otherUserElement = document.querySelector('[data-other-user-id]');
            if (otherUserElement) {
                this.otherUserId = otherUserElement.dataset.otherUserId;
            }
        }
        
        console.log('Conversation Data:', {
            conversationId: this.currentConversationId,
            currentUserId: this.currentUserId,
            otherUserId: this.otherUserId
        });
    }

    bindEvents() {
        // Send message on Enter key
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // Typing indicator
            messageInput.addEventListener('input', () => {
                this.handleTyping();
            });
        }

        // Send button
        const sendButton = document.getElementById('sendButton');
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }

        // Call buttons - FIXED: Use proper selectors
        document.querySelectorAll('[onclick*="initiateCall"]').forEach(btn => {
            btn.removeAttribute('onclick');
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const callType = btn.classList.contains('video-call') ? 'video' : 'voice';
                this.initiateCall(callType);
            });
        });

        // Or if buttons have specific IDs
        const voiceCallBtn = document.querySelector('[title*="Voice"]');
        if (voiceCallBtn) {
            voiceCallBtn.addEventListener('click', () => this.initiateCall('voice'));
        }

        const videoCallBtn = document.querySelector('[title*="Video"]');
        if (videoCallBtn) {
            videoCallBtn.addEventListener('click', () => this.initiateCall('video'));
        }

        // Emoji picker
        const emojiBtn = document.querySelector('[title*="Emoji"], .emoji-btn, [onclick*="toggleEmojiPicker"]');
        if (emojiBtn) {
            emojiBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleEmojiPicker();
            });
        }

        // More options menu
        const moreOptionsBtn = document.querySelector('[title*="More options"], .more-options-btn');
        if (moreOptionsBtn) {
            moreOptionsBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMoreOptions();
            });
        }

        // File upload
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
    }

    initializeSocketIO() {
        try {
            // Load Socket.IO if not already loaded
            if (typeof io === 'undefined') {
                console.log('Socket.IO not loaded, loading now...');
                const script = document.createElement('script');
                script.src = 'https://cdn.socket.io/4.5.0/socket.io.min.js';
                script.onload = () => this.setupSocketConnection();
                document.head.appendChild(script);
            } else {
                this.setupSocketConnection();
            }
        } catch (error) {
            console.error('Socket.IO initialization error:', error);
        }
    }

    setupSocketConnection() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('Connected to messaging server');
                if (this.currentConversationId) {
                    this.joinConversation(this.currentConversationId);
                }
            });

            this.socket.on('disconnect', () => {
                console.log('Disconnected from messaging server');
            });

            // Message events
            this.socket.on('new_message', (data) => {
                console.log('New message received:', data);
                this.handleNewMessage(data);
            });

            this.socket.on('user_typing', (data) => {
                this.handleTypingIndicator(data);
            });

            // Call events
            this.socket.on('incoming_call', (data) => {
                console.log('Incoming call:', data);
                this.handleIncomingCall(data);
            });

            this.socket.on('call_answered', (data) => {
                console.log('Call answered:', data);
                this.handleCallAnswered(data);
            });

            this.socket.on('call_ended', (data) => {
                console.log('Call ended:', data);
                this.handleCallEnded(data);
            });

        } catch (error) {
            console.error('Socket connection error:', error);
        }
    }

    joinConversation(conversationId) {
        if (this.socket && conversationId) {
            this.socket.emit('join_conversation', {
                conversation_id: conversationId
            });
            console.log(`Joined conversation ${conversationId}`);
        }
    }

    loadMessages() {
        if (!this.currentConversationId) {
            console.error('No conversation ID to load messages');
            return;
        }
        
        console.log(`Loading messages for conversation ${this.currentConversationId}`);
        
        fetch(`/messages/api/conversation/${this.currentConversationId}/messages`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Messages loaded:', data);
                if (data.success) {
                    this.displayMessages(data.messages);
                    this.markMessagesAsRead();
                } else {
                    console.error('Failed to load messages:', data.message);
                }
            })
            .catch(error => {
                console.error('Error loading messages:', error);
            });
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const content = messageInput ? messageInput.value.trim() : '';
        
        if (!content) {
            this.showNotification('Message cannot be empty', 'error');
            return;
        }
        
        console.log(`Sending message to conversation ${this.currentConversationId}:`, content);
        
        try {
            const formData = new FormData();
            formData.append('content', content);
            formData.append('conversation_id', this.currentConversationId);
            formData.append('message_type', 'text');
            
            const response = await fetch(`/messages/send_message/${this.currentConversationId}`, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            console.log('Send message response:', data);
            
            if (data.success) {
                if (messageInput) {
                    messageInput.value = '';
                    messageInput.style.height = 'auto';
                }
                
                this.stopTyping();
                this.showNotification('Message sent', 'success');
                
                // Add message to UI immediately
                if (data.message_data) {
                    this.addMessageToUI(data.message_data, true);
                }
            } else {
                this.showNotification(data.message || 'Error sending message', 'error');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showNotification('Error sending message. Please try again.', 'error');
        }
    }

    async initiateCall(callType) {
        if (!this.otherUserId) {
            console.error('Cannot make call: other user ID not found');
            this.showNotification('Cannot make call', 'error');
            return;
        }
        
        console.log(`Initiating ${callType} call to user ${this.otherUserId}`);
        
        try {
            const response = await fetch('/messages/api/initiate_call', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    receiver_id: this.otherUserId,
                    call_type: callType
                })
            });
            
            const data = await response.json();
            console.log('Initiate call response:', data);
            
            if (data.success) {
                this.showCallModal('outgoing', callType, data.session_id);
                this.showNotification('Call initiated', 'success');
            } else {
                this.showNotification(data.message || 'Error initiating call', 'error');
            }
        } catch (error) {
            console.error('Error initiating call:', error);
            this.showNotification('Error initiating call. Please try again.', 'error');
        }
    }

    showCallModal(type, callType, sessionId = null, callerName = null) {
        // Create modal if it doesn't exist
        let modal = document.getElementById('callModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'callModal';
            modal.className = 'call-modal hidden';
            modal.innerHTML = `
                <div class="call-content" id="callContent"></div>
            `;
            document.body.appendChild(modal);
        }
        
        const callContent = document.getElementById('callContent');
        
        if (type === 'outgoing') {
            const chatUserName = document.getElementById('chatUserName');
            const userName = chatUserName ? chatUserName.textContent : 'User';
            
            callContent.innerHTML = `
                <div class="call-outgoing">
                    <div class="call-avatar">
                        <i class="fas fa-phone text-4xl"></i>
                    </div>
                    <h3 class="call-title">Calling ${userName}</h3>
                    <p class="call-subtitle">${callType === 'video' ? 'Video call' : 'Voice call'}...</p>
                    <div class="call-timer" id="callTimer">00:00</div>
                    <div class="call-controls">
                        <button class="call-control-btn end-call" onclick="messenger.endCall()">
                            <i class="fas fa-phone-slash"></i>
                        </button>
                    </div>
                </div>
            `;
        } else if (type === 'incoming') {
            callContent.innerHTML = `
                <div class="call-incoming">
                    <div class="call-avatar">
                        <i class="fas fa-phone text-4xl"></i>
                    </div>
                    <h3 class="call-title">Incoming ${callType === 'video' ? 'Video' : 'Voice'} Call</h3>
                    <p class="call-subtitle">From: ${callerName || 'User'}</p>
                    <div class="call-controls">
                        <button class="call-control-btn answer-call" onclick="messenger.answerCall('${sessionId}')">
                            <i class="fas fa-phone"></i>
                        </button>
                        <button class="call-control-btn decline-call" onclick="messenger.rejectCall('${sessionId}')">
                            <i class="fas fa-phone-slash"></i>
                        </button>
                    </div>
                </div>
            `;
        }
        
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }

    handleTyping() {
        if (!this.isTyping && this.socket && this.currentConversationId) {
            this.isTyping = true;
            this.socket.emit('typing', {
                conversation_id: this.currentConversationId
            });
        }
        
        clearTimeout(this.typingTimeout);
        this.typingTimeout = setTimeout(() => {
            this.stopTyping();
        }, 1000);
    }

    stopTyping() {
        if (this.isTyping && this.socket && this.currentConversationId) {
            this.isTyping = false;
            this.socket.emit('stop_typing', {
                conversation_id: this.currentConversationId
            });
        }
    }

    toggleEmojiPicker() {
        // Create emoji picker if it doesn't exist
        let picker = document.getElementById('emojiPicker');
        if (!picker) {
            picker = document.createElement('div');
            picker.id = 'emojiPicker';
            picker.className = 'emoji-picker hidden';
            
            // Add emojis
            const emojis = ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈', '👿', '👹', '👺', '🤡', '💩', '👻', '💀', '☠️', '👽', '👾', '🤖', '🎃', '😺', '😸', '😹', '😻', '😼', '😽', '🙀', '😿', '😾'];
            
            const emojiGrid = document.createElement('div');
            emojiGrid.className = 'emoji-grid';
            
            emojis.forEach(emoji => {
                const emojiBtn = document.createElement('button');
                emojiBtn.className = 'emoji-item';
                emojiBtn.textContent = emoji;
                emojiBtn.addEventListener('click', () => this.addEmoji(emoji));
                emojiGrid.appendChild(emojiBtn);
            });
            
            picker.appendChild(emojiGrid);
            document.querySelector('.message-input-container').appendChild(picker);
        }
        
        picker.classList.toggle('hidden');
    }

    addEmoji(emoji) {
        const input = document.getElementById('messageInput');
        if (input) {
            input.value += emoji;
            input.focus();
        }
        this.toggleEmojiPicker();
    }

    toggleMoreOptions() {
        // Create more options menu if it doesn't exist
        let menu = document.getElementById('moreOptionsMenu');
        if (!menu) {
            menu = document.createElement('div');
            menu.id = 'moreOptionsMenu';
            menu.className = 'more-options-menu hidden';
            menu.innerHTML = `
                <button class="menu-item" onclick="messenger.clearChat()">
                    <i class="fas fa-trash"></i> Clear Chat
                </button>
                <button class="menu-item" onclick="messenger.blockUser()">
                    <i class="fas fa-ban"></i> Block User
                </button>
                <button class="menu-item" onclick="messenger.reportChat()">
                    <i class="fas fa-flag"></i> Report
                </button>
                <button class="menu-item" onclick="messenger.exportChat()">
                    <i class="fas fa-download"></i> Export Chat
                </button>
            `;
            document.querySelector('.chat-header').appendChild(menu);
        }
        
        menu.classList.toggle('hidden');
    }

    // Event handlers
    handleNewMessage(data) {
        console.log('New message data:', data);
        if (data.conversation_id == this.currentConversationId) {
            this.addMessageToUI(data.message_data, true);
            this.scrollToBottom();
            this.markMessagesAsRead();
        }
    }

    handleTypingIndicator(data) {
        if (data.conversation_id == this.currentConversationId) {
            this.showTypingIndicator(data.user_name);
        }
    }

    handleIncomingCall(data) {
        this.showCallModal('incoming', data.call_type, data.session_id, data.caller_name);
    }

    handleCallAnswered(data) {
        // Update call modal to show call answered
        const callContent = document.getElementById('callContent');
        if (callContent) {
            callContent.querySelector('.call-subtitle').textContent = 'Call connected';
        }
    }

    handleCallEnded(data) {
        // Close call modal
        const modal = document.getElementById('callModal');
        if (modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    }

    // UI Methods
    addMessageToUI(messageData, isNew = false) {
        const container = document.getElementById('messagesContainer');
        if (!container) return;
        
        const messageElement = this.createMessageElement(messageData);
        container.appendChild(messageElement);
        
        if (isNew) {
            this.scrollToBottom();
        }
    }

    createMessageElement(message) {
        const isCurrentUser = message.sender_id == this.currentUserId;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-wrapper ${isCurrentUser ? 'message-sent' : 'message-received'}`;
        messageDiv.id = `message-${message.id}`;
        
        let contentHTML = '';
        
        // Message content
        if (message.message_type === 'text') {
            contentHTML += `<div class="message-text">${this.escapeHtml(message.content)}</div>`;
        } else {
            contentHTML += `<div class="message-text"><i>${message.message_type} file</i></div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-bubble">
                ${!isCurrentUser ? `
                    <div class="message-sender">${this.escapeHtml(message.sender_name)}</div>
                ` : ''}
                
                ${contentHTML}
                
                <div class="message-footer">
                    <span class="message-time">${message.formatted_time}</span>
                    ${isCurrentUser ? `
                        <span class="message-status">
                            ${message.is_read ? '✓✓' : '✓'}
                        </span>
                    ` : ''}
                </div>
            </div>
        `;
        
        return messageDiv;
    }

    displayMessages(messages) {
        const container = document.getElementById('messagesContainer');
        if (!container) {
            console.error('Messages container not found');
            return;
        }
        
        container.innerHTML = '';
        
        if (messages.length === 0) {
            container.innerHTML = '<div class="no-messages">No messages yet. Start the conversation!</div>';
            return;
        }
        
        messages.forEach(message => {
            const messageElement = this.createMessageElement(message);
            container.appendChild(messageElement);
        });
        
        this.scrollToBottom();
    }

    scrollToBottom() {
        const messagesArea = document.getElementById('messagesArea');
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    }

    markMessagesAsRead() {
        if (!this.currentConversationId) return;
        
        fetch(`/messages/api/mark_as_read/${this.currentConversationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(error => console.error('Error marking messages as read:', error));
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        document.querySelectorAll('.notification').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    showTypingIndicator(userName) {
        const typingIndicator = document.getElementById('typingIndicator');
        const typingUserName = document.getElementById('typingUserName');
        
        if (typingIndicator && typingUserName) {
            typingUserName.textContent = `${userName} is typing...`;
            typingIndicator.classList.remove('hidden');
            
            setTimeout(() => {
                if (typingIndicator) {
                    typingIndicator.classList.add('hidden');
                }
            }, 3000);
        }
    }

    // Utility methods
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // API methods
    answerCall(sessionId) {
        fetch('/messages/api/answer_call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
    }

    rejectCall(sessionId) {
        fetch('/messages/api/reject_call', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const modal = document.getElementById('callModal');
        if (modal) modal.classList.add('hidden');
    }

    endCall() {
        const modal = document.getElementById('callModal');
        if (modal) modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    }

    // Menu actions
    clearChat() {
        if (confirm('Are you sure you want to clear this chat?')) {
            fetch(`/messages/api/delete_conversation/${this.currentConversationId}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }).then(() => {
                window.location.href = '/messages/inbox';
            });
        }
    }

    blockUser() {
        alert('Block user feature coming soon!');
    }

    reportChat() {
        alert('Report feature coming soon!');
    }

    exportChat() {
        alert('Export chat feature coming soon!');
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.messenger = new FixedMessenger();
});

// Global functions for HTML onclick attributes
window.addEmoji = function(emoji) {
    if (window.messenger) window.messenger.addEmoji(emoji);
};

window.toggleEmojiPicker = function() {
    if (window.messenger) window.messenger.toggleEmojiPicker();
};

window.initiateCall = function(callType) {
    if (window.messenger) window.messenger.initiateCall(callType);
};

window.toggleMoreOptions = function() {
    if (window.messenger) window.messenger.toggleMoreOptions();
};