// Profile Picture Upload Functionality

// Get CSRF Token from meta tag
function getCsrfToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.content : '';
}

async function uploadProfilePicture(file) {
    if (!file) return;
    
    console.log('Starting upload for:', file.name, file.size, file.type);
    
    // Validate file
    if (file.size > 5 * 1024 * 1024) {
        alert('File too large (max 5MB)');
        return;
    }
    
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
        alert('Please select JPEG, PNG, GIF, or WebP image');
        return;
    }
    
    const formData = new FormData();
    formData.append('profile_picture', file);
    
    // Show loading state
    const button = document.querySelector('[onclick*="profile-picture-input"]');
    const originalHTML = button ? button.innerHTML : '<i class="fas fa-camera"></i>';
    if (button) {
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
    }
    
    try {
        console.log('Sending upload request to /profile/api/upload-profile-picture');
        
        // IMPORTANT: Add CSRF token to headers
        const response = await fetch('/profile/api/upload-profile-picture', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        });
        
        console.log('Response status:', response.status);
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text.substring(0, 500));
            throw new Error('Server error: ' + text.substring(0, 100));
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!response.ok) {
            throw new Error(data.message || `HTTP ${response.status}`);
        }
        
        if (data.success) {
            // Update UI
            updateProfilePicture(data.file_url);
            showNotification('Profile picture updated!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error(data.message || 'Upload failed');
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        alert('Upload failed: ' + error.message);
    } finally {
        // Restore button
        if (button) {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }
}

function updateProfilePicture(imageUrl) {
    // Add timestamp to bypass cache
    const timestamp = '?t=' + new Date().getTime();
    const fullUrl = imageUrl + timestamp;
    
    // Update preview in edit page
    let preview = document.getElementById('profile-preview');
    if (preview) {
        preview.src = fullUrl;
    }
    
    // Update header avatar
    const headerImg = document.querySelector('#header-user-dropdown img');
    if (headerImg) {
        headerImg.src = fullUrl;
    }
    
    // Update profile page avatar
    const profileAvatar = document.querySelector('#profile-avatar');
    if (profileAvatar) {
        profileAvatar.src = fullUrl;
    }
    
    // Update profile avatar container (for fallback)
    const profileAvatarContainer = document.querySelector('.w-28.h-28 img');
    if (profileAvatarContainer) {
        profileAvatarContainer.src = fullUrl;
    }
    
    // Update any other profile picture elements
    const profileImages = document.querySelectorAll('img[src*="profile_pictures"]');
    profileImages.forEach(img => {
        if (img.id !== 'profile-preview') {
            img.src = fullUrl;
        }
    });
    
    console.log('Profile picture updated in UI');
}

function showNotification(message, type = 'success') {
    // Remove existing notification
    const existing = document.querySelector('.fixed-notification');
    if (existing) existing.remove();
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `fixed-notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 transition-all duration-300 ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    }`;
    notification.textContent = message;
    notification.style.right = '-300px';
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.right = '16px';
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.right = '-300px';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// At the bottom of profile-upload.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Profile upload JavaScript initializing...');
    
    // Check for profile picture input
    const profileInput = document.getElementById('profile-picture-input');
    if (profileInput) {
        console.log('Profile picture input found');
        // Your existing code here
    } else {
        console.log('Profile picture input not found (only needed on profile page)');
    }
});