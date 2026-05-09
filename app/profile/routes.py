from flask import render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Post, Friendship, Notification, QuizResult, Topic
from app.profile.forms import ProfileForm, CoverPhotoForm
from app.profile import profile_bp
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date, timedelta
from sqlalchemy import func

@profile_bp.route('/profile/<int:user_id>')
@login_required
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user's posts
    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id=user_id).order_by(
    Post.created_at.desc()
).all()
    
    # Get user's quiz stats
    quiz_stats = QuizResult.query.filter_by(user_id=user_id).all()
    total_quizzes = len(quiz_stats)
    average_score = sum(quiz.score for quiz in quiz_stats) / total_quizzes if total_quizzes > 0 else 0
    
    # ========== TOPIC MASTERY - SAME AS DASHBOARD ==========
    # Get all topics
    topics = Topic.query.all()
    
    # If no topics exist in database, use these defaults
    if not topics:
        default_topics = [
            {'name': 'Farm Machinery', 'icon': 'fas fa-tractor'},
            {'name': 'Soil & Water Management', 'icon': 'fas fa-tint'},
            {'name': 'Post-Harvest Technology', 'icon': 'fas fa-boxes'},
            {'name': 'Environmental Engineering', 'icon': 'fas fa-industry'},
            {'name': 'PAES Standards', 'icon': 'fas fa-file-alt'},
            {'name': 'Engineering Mathematics', 'icon': 'fas fa-calculator'},
        ]
        topic_scores = []
        for default in default_topics:
            topic_scores.append({
                'id': 0,
                'name': default['name'],
                'score': 0,
                'icon': default['icon'],
                'color': '#4CAF50'
            })
    else:
        # Calculate average score for each topic from database
        topic_scores = []
        for topic in topics:
            topic_results = QuizResult.query.filter_by(
                user_id=user_id,
                topic_id=topic.id
            ).all()
            
            if topic_results:
                total_score = sum((result.score or 0) for result in topic_results)
                avg_score = round(total_score / len(topic_results), 2)
            else:
                avg_score = 0
                
            topic_scores.append({
                'id': topic.id,
                'name': topic.name,
                'score': avg_score,
                'icon': topic.icon if hasattr(topic, 'icon') else 'fas fa-book',
                'color': topic.color if hasattr(topic, 'color') else '#4CAF50'
            })
    
    # Check friendship status
    friendship = None
    if user_id != current_user.id:
        friendship = Friendship.query.filter(
            ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)) |
            ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id))
        ).first()
    
    return render_template('profile/profile.html',
                         user=user,
                         posts=posts,
                         total_quizzes=total_quizzes,
                         average_score=round(average_score, 2),
                         friendship=friendship,
                         topic_scores=topic_scores,
                         title=f'{user.name} - Profile')

@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.bio = form.bio.data
        current_user.location = form.location.data
        current_user.website = form.website.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view_profile', user_id=current_user.id))
    
    return render_template('profile/edit_profile.html',
                         form=form,
                         title='Edit Profile')

@profile_bp.route('/api/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    try:
        print("=== UPLOAD PROFILE PICTURE ENDPOINT HIT ===")
        
        if 'profile_picture' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['profile_picture']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if not file:
            return jsonify({'success': False, 'message': 'Invalid file'}), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'Invalid file type. Only PNG, JPG, JPEG, GIF allowed.'}), 400
        
        # Generate secure filename
        timestamp = int(datetime.now().timestamp())
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
        filename = f"profile_{current_user.id}_{timestamp}.{file_ext}"
        
        # Create upload directory using absolute path
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # Verify file was saved
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': 'Failed to save file'}), 500
        
        # Remove old profile picture if exists
        if current_user.profile_picture:
            old_file_path = os.path.join(upload_dir, current_user.profile_picture)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        # Update user in database
        current_user.profile_picture = filename
        db.session.commit()
        
        # Generate file URL
        file_url = url_for('static', filename=f'uploads/profile_pictures/{filename}', _external=False)
        
        return jsonify({
            'success': True, 
            'message': 'Profile picture uploaded successfully!', 
            'filename': filename,
            'file_url': file_url
        })
        
    except Exception as e:
        print(f"UPLOAD ERROR: {str(e)}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@profile_bp.route('/api/debug-upload', methods=['GET'])
@login_required
def debug_upload():
    """Debug endpoint to check upload directory"""
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
    
    debug_info = {
        'app_root': current_app.root_path,
        'upload_dir': upload_dir,
        'dir_exists': os.path.exists(upload_dir),
        'dir_writable': os.access(upload_dir, os.W_OK) if os.path.exists(upload_dir) else False,
        'current_user_id': current_user.id,
        'current_profile_pic': current_user.profile_picture
    }
    
    return jsonify(debug_info)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_bp.route('/api/upload-cover-photo', methods=['POST'])
@login_required
def upload_cover_photo():
    if 'cover_photo' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['cover_photo']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f"cover_{current_user.id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'cover_photos')
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, filename)
        file.save(file_path)
        
        # Remove old cover photo if exists
        if current_user.cover_photo:
            old_file_path = os.path.join(upload_path, current_user.cover_photo)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        
        current_user.cover_photo = filename
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cover photo uploaded successfully', 'filename': filename})
    else:
        return jsonify({'success': False, 'message': 'Invalid file type'}), 400

@profile_bp.route('/api/send-friend-request/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot send friend request to yourself'}), 400
    
    user = User.query.get_or_404(user_id)
    
    # Check if friendship already exists
    existing_friendship = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if existing_friendship:
        return jsonify({'success': False, 'message': 'Friend request already exists'}), 400
    
    friendship = Friendship(user_id=current_user.id, friend_id=user_id)
    db.session.add(friendship)
    
    # Create notification
    notification = Notification(
        user_id=user_id,
        title='Friend Request',
        message=f'{current_user.name} sent you a friend request',
        notification_type='friend_request',
        related_id=current_user.id
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Friend request sent successfully'})

@profile_bp.route('/api/accept-friend-request/<int:friendship_id>', methods=['POST'])
@login_required
def accept_friend_request(friendship_id):
    friendship = Friendship.query.get_or_404(friendship_id)
    
    if friendship.friend_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    friendship.status = 'accepted'
    
    # Create notification
    notification = Notification(
        user_id=friendship.user_id,
        title='Friend Request Accepted',
        message=f'{current_user.name} accepted your friend request',
        notification_type='friend_request_accepted',
        related_id=current_user.id
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Friend request accepted'})

@profile_bp.route('/api/reject-friend-request/<int:friendship_id>', methods=['POST'])
@login_required
def reject_friend_request(friendship_id):
    friendship = Friendship.query.get_or_404(friendship_id)
    
    if friendship.friend_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(friendship)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Friend request rejected'})

@profile_bp.route('/api/remove-friend/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    friendship = Friendship.query.filter(
        ((Friendship.user_id == current_user.id) & (Friendship.friend_id == user_id)) |
        ((Friendship.user_id == user_id) & (Friendship.friend_id == current_user.id))
    ).first()
    
    if not friendship:
        return jsonify({'success': False, 'message': 'Friendship not found'}), 404
    
    db.session.delete(friendship)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Friend removed successfully'})

@profile_bp.route('/my-profile')
@login_required
def my_profile():
    """Redirect to current user's profile"""
    return redirect(url_for('profile.view_profile', user_id=current_user.id))

@profile_bp.route('/api/quick-profile/<int:user_id>')
@login_required
def quick_profile(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user stats
    posts_count = Post.query.filter_by(user_id=user_id).count()
    friends_count = user.friends_count
    quizzes_taken = QuizResult.query.filter_by(user_id=user_id).count()
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'name': user.name,
            'bio': user.bio,
            'profile_picture': user.profile_picture,
            'posts_count': posts_count,
            'friends_count': friends_count,
            'quizzes_taken': quizzes_taken
        }
    })

# ============ CREATE POST API ENDPOINT - ADD THIS ============
@profile_bp.route('/api/create_post', methods=['POST'])
@login_required
def create_post_api():
    """API endpoint to create a new post"""
    try:
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        post_type = request.form.get('post_type', 'discussion')
        
        if not content:
            return jsonify({'success': False, 'message': 'Content is required'}), 400
        
        # Handle media file upload
        media_file = None
        if 'media_file' in request.files:
            file = request.files['media_file']
            if file and file.filename and allowed_file(file.filename):
                timestamp = int(datetime.now().timestamp())
                file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
                filename = f"post_{current_user.id}_{timestamp}.{file_ext}"
                
                upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'post_images')
                os.makedirs(upload_dir, exist_ok=True)
                
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                media_file = filename
        
        # Create post
        post = Post(
            title=title if title else None,
            content=content,
            user_id=current_user.id,
            post_type=post_type,
            media_file=media_file,
            media_type='image' if media_file else None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Post created successfully!'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating post: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500