// app/static/js/profile.js - Complete profile interactions

// ============ CSRF Token Helper ============
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

// ============ Show Toast Notification ============
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
    const icon = type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle';
    
    toast.className = `fixed bottom-4 right-4 z-50 ${bgColor} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 transform transition-all duration-300 translate-x-full`;
    toast.innerHTML = `<i class="fas ${icon}"></i><span>${message}</span>`;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('translate-x-full');
    }, 100);
    
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============ Profile Picture Upload ============
async function uploadProfilePicture(file) {
    if (!file) return;
    
    // Validate file
    if (file.size > 5 * 1024 * 1024) {
        showToast('File too large (max 5MB)', 'error');
        return;
    }
    
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        showToast('Please select JPEG, PNG, GIF, or WebP image', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('profile_picture', file);
    
    // Show loading state
    const button = document.querySelector('[onclick*="profile-picture-input"]');
    const originalHTML = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    button.disabled = true;
    
    try {
        const response = await fetch('/profile/api/upload-profile-picture', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateProfilePicture(data.file_url);
            showToast('Profile picture updated!', 'success');
        } else {
            throw new Error(data.message || 'Upload failed');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showToast(error.message, 'error');
    } finally {
        button.innerHTML = originalHTML;
        button.disabled = false;
    }
}

function updateProfilePicture(imageUrl) {
    // Update preview in edit page
    let preview = document.getElementById('profile-preview');
    if (preview) {
        preview.src = imageUrl + '?t=' + new Date().getTime();
    }
    
    // Update profile page avatar
    const profileAvatar = document.querySelector('.w-24.h-24 img');
    if (profileAvatar) {
        profileAvatar.src = imageUrl + '?t=' + new Date().getTime();
    }
    
    // Update header
    const headerImg = document.querySelector('#header-user-dropdown img');
    if (headerImg) {
        headerImg.src = imageUrl + '?t=' + new Date().getTime();
    }
}

// ============ Friend Request Functions ============
async function sendFriendRequest(userId) {
    try {
        const response = await fetch(`/profile/api/send-friend-request/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        showToast(data.message, data.success ? 'success' : 'error');
        if (data.success) setTimeout(() => location.reload(), 1500);
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to send friend request', 'error');
    }
}

async function acceptFriendRequest(friendshipId) {
    try {
        const response = await fetch(`/profile/api/accept-friend-request/${friendshipId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        showToast(data.message, 'success');
        if (data.success) setTimeout(() => location.reload(), 1500);
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to accept request', 'error');
    }
}

async function rejectFriendRequest(friendshipId) {
    try {
        const response = await fetch(`/profile/api/reject-friend-request/${friendshipId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        showToast(data.message, 'info');
        if (data.success) setTimeout(() => location.reload(), 1500);
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to reject request', 'error');
    }
}

async function removeFriend(userId) {
    if (!confirm('Are you sure you want to remove this friend?')) return;
    
    try {
        const response = await fetch(`/profile/api/remove-friend/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        showToast(data.message, data.success ? 'success' : 'error');
        if (data.success) setTimeout(() => location.reload(), 1500);
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to remove friend', 'error');
    }
}

// ============ Message Button Function ============
async function startConversation(userId) {
    try {
        const response = await fetch(`/messages/start_conversation/${userId}`);
        
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const data = await response.json();
            if (data.conversation_id) {
                window.location.href = `/messages/conversation/${data.conversation_id}`;
            }
        }
    } catch (error) {
        console.error('Error starting conversation:', error);
        // Fallback redirect
        window.location.href = `/messages/start_conversation/${userId}`;
    }
}

// ============ Cover Photo Functions ============
function openCoverPhotoUpload() {
    const modal = document.getElementById('coverPhotoModal');
    if (modal) modal.classList.remove('hidden');
}

function closeCoverPhotoUpload() {
    const modal = document.getElementById('coverPhotoModal');
    if (modal) modal.classList.add('hidden');
}

async function uploadCoverPhoto() {
    const fileInput = document.getElementById('coverPhotoInput');
    const file = fileInput?.files[0];
    
    if (!file) {
        showToast('Please select a file', 'error');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        showToast('File size must be less than 5MB', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('cover_photo', file);
    
    try {
        const response = await fetch('/profile/api/upload-cover-photo', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('Cover photo updated!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to upload cover photo', 'error');
    }
}

// ============ Post Functions ============
async function likePost(postId) {
    try {
        const response = await fetch(`/community/api/like/${postId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            const likeIcon = document.getElementById(`like-icon-${postId}`);
            const likeCount = document.getElementById(`like-count-${postId}`);
            
            if (likeCount) likeCount.textContent = data.like_count;
            if (likeIcon) {
                if (data.liked) {
                    likeIcon.classList.add('text-red-600');
                } else {
                    likeIcon.classList.remove('text-red-600');
                }
            }
        }
    } catch (error) {
        console.error('Error liking post:', error);
    }
}

function toggleComments(postId) {
    const commentsSection = document.getElementById(`comments-section-${postId}`);
    if (commentsSection) {
        commentsSection.classList.toggle('hidden');
        if (!commentsSection.classList.contains('hidden')) {
            loadComments(postId);
        }
    }
}

async function loadComments(postId) {
    try {
        const response = await fetch(`/community/api/get_comments/${postId}`);
        const data = await response.json();
        
        if (data.success) {
            const commentsList = document.getElementById(`comments-list-${postId}`);
            if (!commentsList) return;
            
            commentsList.innerHTML = '';
            
            if (data.comments.length === 0) {
                commentsList.innerHTML = '<p class="text-gray-500 text-center py-4">No comments yet</p>';
                return;
            }
            
            data.comments.forEach(comment => {
                const commentElement = createCommentElement(comment);
                commentsList.appendChild(commentElement);
            });
        }
    } catch (error) {
        console.error('Error loading comments:', error);
    }
}

function createCommentElement(comment) {
    const commentDiv = document.createElement('div');
    commentDiv.className = 'flex items-start space-x-3 p-3 bg-gray-50 rounded-lg';
    commentDiv.id = `comment-${comment.id}`;
    
    const currentUserId = parseInt(document.body.dataset.userId || '0');
    const isAuthor = comment.author_id === currentUserId;
    
    commentDiv.innerHTML = `
        <div class="w-6 h-6 bg-green-400 rounded-full flex items-center justify-center flex-shrink-0">
            ${comment.author_profile_picture ? 
                `<img src="/static/uploads/profile_pictures/${comment.author_profile_picture}" class="w-6 h-6 rounded-full object-cover">` :
                `<i class="fas fa-user text-white text-xs"></i>`
            }
        </div>
        <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium text-gray-900">${escapeHtml(comment.author_name)}</span>
                <span class="text-xs text-gray-500">${new Date(comment.created_at).toLocaleDateString()}</span>
            </div>
            <p class="text-sm text-gray-700 mb-2" id="comment-content-${comment.id}">${escapeHtml(comment.content)}</p>
            
            <div class="flex items-center space-x-4 text-xs">
                <button onclick="likeComment(${comment.id})" 
                        class="flex items-center space-x-1 text-gray-500 hover:text-red-600 transition-colors">
                    <i class="fas fa-heart ${comment.user_liked ? 'text-red-600' : ''}"></i>
                    <span>${comment.like_count || 0}</span>
                </button>
                
                ${isAuthor ? `
                <button onclick="editComment(${comment.id})" 
                        class="text-blue-600 hover:text-blue-800 transition-colors">
                    Edit
                </button>
                <button onclick="deleteComment(${comment.id})" 
                        class="text-red-600 hover:text-red-800 transition-colors">
                    Delete
                </button>
                ` : ''}
            </div>
        </div>
    `;
    
    return commentDiv;
}

async function addComment(event, postId) {
    event.preventDefault();
    
    const commentInput = document.getElementById(`comment-input-${postId}`);
    const content = commentInput?.value.trim();
    
    if (!content) {
        showToast('Please write a comment', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/community/api/add_comment/${postId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ content: content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            commentInput.value = '';
            loadComments(postId);
            
            // Update comment count
            const commentBtn = document.querySelector(`[onclick="toggleComments(${postId})"] span`);
            if (commentBtn) {
                const currentCount = parseInt(commentBtn.textContent) || 0;
                commentBtn.textContent = currentCount + 1;
            }
        } else {
            showToast(data.message || 'Error adding comment', 'error');
        }
    } catch (error) {
        console.error('Error adding comment:', error);
        showToast('Error adding comment', 'error');
    }
}

function sharePost(postId) {
    const url = `${window.location.origin}/community/post/${postId}`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Check out this post',
            url: url
        }).catch(() => copyToClipboard(url));
    } else {
        copyToClipboard(url);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Link copied to clipboard!', 'success');
    }).catch(() => {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('Link copied to clipboard!', 'success');
    });
}

// ============ Post Menu Functions ============
function togglePostActions(postId) {
    const menu = document.getElementById(`post-actions-${postId}`);
    if (!menu) return;
    
    // Close all other menus
    document.querySelectorAll('[id^="post-actions-"]').forEach(otherMenu => {
        if (otherMenu.id !== `post-actions-${postId}`) {
            otherMenu.classList.add('hidden');
        }
    });
    
    menu.classList.toggle('hidden');
}

// Close menus when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('[id^="post-actions-"]') && 
        !e.target.closest('[onclick*="togglePostActions"]')) {
        document.querySelectorAll('[id^="post-actions-"]').forEach(menu => {
            menu.classList.add('hidden');
        });
    }
});

// ============ Edit/Delete Post Functions ============
let currentEditingPostId = null;

async function editPost(postId) {
    try {
        const response = await fetch(`/community/api/get_post/${postId}`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('editPostTitle').value = data.data.title || '';
            document.getElementById('editPostContent').value = data.data.content;
            currentEditingPostId = postId;
            document.getElementById('editPostModal').classList.remove('hidden');
        } else {
            showToast('Error loading post', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error loading post', 'error');
    }
}

function closeEditPostModal() {
    document.getElementById('editPostModal').classList.add('hidden');
    currentEditingPostId = null;
}

async function savePostChanges(event) {
    if (event) event.preventDefault();
    
    if (!currentEditingPostId) return;
    
    const title = document.getElementById('editPostTitle').value.trim();
    const content = document.getElementById('editPostContent').value.trim();
    
    if (!content) {
        showToast('Post content is required', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/community/api/edit_post/${currentEditingPostId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ title: title, content: content })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Post updated successfully!', 'success');
            closeEditPostModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message || 'Error updating post', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error updating post', 'error');
    }
}

async function deletePost(postId) {
    if (!confirm('Are you sure you want to delete this post? This cannot be undone.')) return;
    
    try {
        const response = await fetch(`/community/api/delete_post/${postId}`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Post deleted successfully', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message || 'Error deleting post', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error deleting post', 'error');
    }
}

// ============ Create Post Functions ============
function openCreatePostModal() {
    document.getElementById('createPostModal').classList.remove('hidden');
}

function closeCreatePostModal() {
    document.getElementById('createPostModal').classList.add('hidden');
    document.getElementById('createPostForm').reset();
}

async function createPost(event) {
    if (event) event.preventDefault();
    
    const title = document.getElementById('postTitle').value.trim();
    const content = document.getElementById('postContent').value.trim();
    const topicId = document.getElementById('postTopic')?.value || 0;
    const mediaFile = document.getElementById('postMedia')?.files[0];
    
    if (!content) {
        showToast('Please write some content', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('title', title);
    formData.append('content', content);
    formData.append('topic_id', topicId);
    formData.append('post_type', 'discussion');
    
    if (mediaFile) {
        if (mediaFile.size > 10 * 1024 * 1024) {
            showToast('File size must be less than 10MB', 'error');
            return;
        }
        formData.append('media_file', mediaFile);
    }
    
    try {
        const response = await fetch('/profile/api/create_post', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Post created successfully!', 'success');
            closeCreatePostModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showToast(data.message || 'Error creating post', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error creating post', 'error');
    }
}

// ============ Helper Functions ============
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ Initialize ============
document.addEventListener('DOMContentLoaded', function() {
    // Set user ID on body for reference
    const userIdElement = document.querySelector('[data-user-id]');
    if (userIdElement) {
        document.body.dataset.userId = userIdElement.dataset.userId;
    }
    
    // Close modals on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeCreatePostModal();
            closeEditPostModal();
            closeCoverPhotoUpload();
        }
    });
});