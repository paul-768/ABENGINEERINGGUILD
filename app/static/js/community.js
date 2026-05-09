// app/static/js/community.js - Complete with working heart reaction and share

// Global CSRF token getter
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg text-white text-sm z-50 transition-all ${type === 'success' ? 'bg-green-600' : 'bg-red-500'}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Like Post (Heart Reaction)
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
            const likeCount = document.getElementById(`like-count-${postId}`);
            const likeIcon = document.getElementById(`like-icon-${postId}`);
            if (likeCount) likeCount.textContent = data.like_count;
            if (likeIcon) {
                if (data.liked) {
                    likeIcon.classList.remove('far', 'fa-heart');
                    likeIcon.classList.add('fas', 'fa-heart', 'text-red-500');
                    // Add heart animation
                    likeIcon.style.transform = 'scale(1.2)';
                    setTimeout(() => {
                        likeIcon.style.transform = 'scale(1)';
                    }, 200);
                } else {
                    likeIcon.classList.remove('fas', 'fa-heart', 'text-red-500');
                    likeIcon.classList.add('far', 'fa-heart');
                }
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to like post', 'error');
    }
}

// Share Post - Copy link to clipboard (WORKING)
async function sharePost(postId) {
    const url = `${window.location.origin}/community/post/${postId}`;
    try {
        await navigator.clipboard.writeText(url);
        showToast('✓ Link copied to clipboard!', 'success');
    } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = url;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        showToast('✓ Link copied to clipboard!', 'success');
    }
}

// Delete Post
async function deletePost(postId) {
    if (!confirm('Are you sure you want to delete this post? This cannot be undone.')) return;
    
    const postCard = document.querySelector(`.post-card[data-post-id="${postId}"]`);
    if (postCard) {
        postCard.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        postCard.style.opacity = '0.5';
        postCard.style.pointerEvents = 'none';
    }
    
    try {
        const response = await fetch(`/community/post/${postId}/delete`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken() 
            }
        });
        const data = await response.json();
        if (data.success) {
            if (postCard) {
                postCard.style.opacity = '0';
                postCard.style.transform = 'translateY(-10px)';
                setTimeout(() => {
                    postCard.remove();
                    showToast('Post deleted successfully', 'success');
                    const remainingPosts = document.querySelectorAll('.post-card').length;
                    if (remainingPosts === 0) {
                        const container = document.getElementById('posts-container');
                        if (container) {
                            container.innerHTML = `
                                <div class="bg-white rounded-xl shadow p-12 text-center">
                                    <i class="fas fa-comments text-gray-300 text-5xl mb-4"></i>
                                    <h3 class="text-lg font-semibold text-gray-900 mb-2">No posts yet</h3>
                                    <p class="text-gray-500">Be the first to start a conversation!</p>
                                </div>
                            `;
                        }
                    }
                }, 300);
            } else {
                location.reload();
            }
        } else {
            showToast(data.message || 'Error deleting post', 'error');
            if (postCard) {
                postCard.style.opacity = '1';
                postCard.style.pointerEvents = '';
            }
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to delete post', 'error');
        if (postCard) {
            postCard.style.opacity = '1';
            postCard.style.pointerEvents = '';
        }
    }
}

// Toggle Post Menu
function togglePostMenu(postId) {
    const menu = document.getElementById(`post-menu-${postId}`);
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

// Filter posts by topic
function filterPostsByTopic(topicId, topicName) {
    const posts = document.querySelectorAll('.post-card');
    let visibleCount = 0;
    posts.forEach(post => {
        const postTopicId = parseInt(post.getAttribute('data-topic-id'));
        if (postTopicId === topicId) {
            post.style.display = '';
            visibleCount++;
        } else {
            post.style.display = 'none';
        }
    });
    const filterBar = document.getElementById('topic-filter-bar');
    if (filterBar) {
        filterBar.classList.remove('hidden');
        document.getElementById('active-topic-name').textContent = topicName;
    }
    showToast(`Showing posts in ${topicName}`, 'success');
}

// Clear topic filter
function clearTopicFilter() {
    document.querySelectorAll('.post-card').forEach(post => post.style.display = '');
    const filterBar = document.getElementById('topic-filter-bar');
    if (filterBar) filterBar.classList.add('hidden');
    showToast('Filter cleared', 'success');
}

// Image Viewer
function openImageViewer(src) {
    const viewer = document.getElementById('imageViewer');
    const viewerImage = document.getElementById('viewerImage');
    if (viewer && viewerImage) {
        viewerImage.src = src;
        viewer.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeImageViewer() {
    const viewer = document.getElementById('imageViewer');
    if (viewer) {
        viewer.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

// Create Post Modal
function openCreatePostModal() {
    const modal = document.getElementById('createPostModal');
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeCreatePostModal() {
    const modal = document.getElementById('createPostModal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
    // Reset form
    const titleInput = document.getElementById('modalPostTitle');
    const contentInput = document.getElementById('modalPostContent');
    const imageInput = document.getElementById('modalImageInput');
    const imagePreview = document.getElementById('modalImagePreview');
    if (titleInput) titleInput.value = '';
    if (contentInput) contentInput.value = '';
    if (imageInput) imageInput.value = '';
    if (imagePreview) imagePreview.classList.add('hidden');
}

function openPostWithType(type) {
    const postTypeInput = document.getElementById('modalPostType');
    if (postTypeInput) postTypeInput.value = type;
    openCreatePostModal();
}

// Image preview for modal
document.addEventListener('DOMContentLoaded', function() {
    const imageInput = document.getElementById('modalImageInput');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            if (e.target.files && e.target.files[0]) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    const previewImg = document.getElementById('modalPreviewImg');
                    const previewDiv = document.getElementById('modalImagePreview');
                    if (previewImg && previewDiv) {
                        previewImg.src = event.target.result;
                        previewDiv.classList.remove('hidden');
                    }
                };
                reader.readAsDataURL(e.target.files[0]);
            }
        });
    }
});

// Close menu when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('[onclick*="togglePostMenu"]') && !e.target.closest('[id^="post-menu-"]')) {
        document.querySelectorAll('[id^="post-menu-"]').forEach(menu => {
            menu.classList.add('hidden');
        });
    }
});

// Escape key handler
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeCreatePostModal();
        closeImageViewer();
    }
});