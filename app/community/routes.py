# app/community/routes.py - COMPLETE FIXED VERSION WITH 9 DISCUSSION ROOMS
from flask import render_template, jsonify, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Post, Comment, Topic, User, Notification, PostLike, Friendship, FriendRequest, SavedPost, GroupChat, GroupMember, GroupMessage, Announcement, CommentLike
from app.community import community_bp
from app.community.forms import PostForm, CommentForm
from app.models import FriendRequest, Friendship, Notification
import uuid
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
import pytz

# Philippine Timezone
PHT = pytz.timezone('Asia/Manila')

def get_ph_time():
    return datetime.now(PHT)

def time_ago(dt):
    if not dt:
        return "Just now"
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    pht_dt = dt.astimezone(PHT)
    now_pht = get_ph_time()
    diff = now_pht - pht_dt
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds > 3600:
        return f"{diff.seconds // 3600}h ago"
    elif diff.seconds > 60:
        return f"{diff.seconds // 60}m ago"
    else:
        return "Just now"

def get_recent_activities(limit=10):
    activities = []
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    for post in recent_posts:
        activities.append({
            'type': 'post',
            'message': f'{post.author.name} created a new {post.post_type}: "{post.title or "post"[:30]}"',
            'timestamp': post.created_at.isoformat(),
            'time_ago': time_ago(post.created_at)
        })
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(3).all()
    for comment in recent_comments:
        activities.append({
            'type': 'comment',
            'message': f'{comment.author.name} commented on a post',
            'timestamp': comment.created_at.isoformat(),
            'time_ago': time_ago(comment.created_at)
        })
    recent_likes = PostLike.query.order_by(PostLike.created_at.desc()).limit(3).all()
    for like in recent_likes:
        post = Post.query.get(like.post_id)
        if post:
            activities.append({
                'type': 'like',
                'message': f'{like.user.name} liked a post by {post.author.name}',
                'timestamp': like.created_at.isoformat(),
                'time_ago': time_ago(like.created_at)
            })
    recent_friendships = Friendship.query.filter(Friendship.status == 'accepted').order_by(Friendship.created_at.desc()).limit(3).all()
    for friendship in recent_friendships:
        user = User.query.get(friendship.user_id)
        friend = User.query.get(friendship.friend_id)
        if user and friend:
            activities.append({
                'type': 'friend',
                'message': f'{user.name} and {friend.name} became friends',
                'timestamp': friendship.created_at.isoformat(),
                'time_ago': time_ago(friendship.created_at)
            })
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return activities[:limit]

@community_bp.route('/api/recent_activity')
@login_required
def get_recent_activity():
    activities = get_recent_activities(limit=10)
    return jsonify({'activities': activities})

@community_bp.route('/api/comments/<int:post_id>')
@login_required
def get_comments_api(post_id):
    """Get comments for a post as JSON"""
    from app.models import Comment, CommentLike
    
    comments = Comment.query.filter_by(post_id=post_id, parent_id=None).order_by(Comment.created_at.asc()).all()
    
    def serialize_comment(comment):
        return {
            'id': comment.id,
            'content': comment.content,
            'author_name': comment.author.name,
            'author_id': comment.author.id,
            'author_avatar': comment.author.get_avatar(),
            'created_at': comment.created_at.isoformat(),
            'time_ago': time_ago(comment.created_at),
            'like_count': comment.like_count(),
            'liked': CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment.id).first() is not None,
            'replies': [serialize_comment(reply) for reply in comment.replies]
        }
    
    return jsonify({
        'success': True,
        'comments': [serialize_comment(c) for c in comments]
    })

@community_bp.route('/')
@login_required
def community_home():
    page = request.args.get('page', 1, type=int)
    topic_filter = request.args.get('topic', type=int)
    query = Post.query.filter(Post.post_type.in_(['discussion', 'question']))
    if topic_filter:
        query = query.filter(Post.topic_id == topic_filter)
    query = query.order_by(Post.created_at.desc())
    posts = query.paginate(page=page, per_page=15, error_out=False)
    topics = Topic.query.all()
    friends = current_user.get_friends() if hasattr(current_user, 'get_friends') else []
    friend_ids = [f.id for f in friends] + [current_user.id]
    suggested_users = User.query.filter(~User.id.in_(friend_ids)).limit(5).all()
    total_users = User.query.count()
    total_posts = Post.query.count()
    one_week_ago = datetime.now(pytz.UTC) - timedelta(days=7)
    weekly_posts = Post.query.filter(Post.created_at >= one_week_ago).count()
    recent_activities = get_recent_activities(limit=9)
    trending_topics = db.session.query(Topic, func.count(Post.id).label('post_count')).join(Post, Post.topic_id == Topic.id).filter(Post.created_at >= one_week_ago).group_by(Topic.id).order_by(func.count(Post.id).desc()).limit(3).all()
    trending_topics_formatted = []
    for topic, count in trending_topics:
        topic.post_count = count
        trending_topics_formatted.append(topic)
    announcements = Announcement.query.filter_by(is_active=True).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).limit(3).all()
    form = PostForm()
    form.topic_id.choices = [(0, 'General')] + [(t.id, t.name) for t in topics]
    return render_template('community/community.html',
                         posts=posts, topics=topics, suggested_users=suggested_users,
                         form=form, total_users=total_users, total_posts=total_posts,
                         weekly_posts=weekly_posts, recent_activities=recent_activities,
                         trending_topics=trending_topics_formatted, announcements=announcements,
                         title='Community')

@community_bp.route('/api/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    existing_like = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    post = Post.query.get(post_id)
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        like = PostLike(user_id=current_user.id, post_id=post_id, created_at=get_ph_time())
        db.session.add(like)
        liked = True
        
        # ========== NOTIFICATION FOR POST LIKE ==========
        if post and post.user_id != current_user.id:
            notification = Notification(
                user_id=post.user_id,
                title="❤️ Someone Liked Your Post",
                message=f"{current_user.name} liked your post: \"{post.content[:50]}...\"",
                notification_type='post_like',
                related_id=post_id,
                related_type='post',
                icon="fas fa-heart",
                action_url=url_for('community.view_post', post_id=post_id),
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
        # ========== END NOTIFICATION ==========
    
    db.session.commit()
    like_count = PostLike.query.filter_by(post_id=post_id).count()
    return jsonify({'success': True, 'liked': liked, 'like_count': like_count})

@community_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    Comment.query.filter_by(post_id=post_id).delete()
    PostLike.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Post deleted successfully'})

@community_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Handle both FormData and urlencoded
    if request.content_type and 'multipart/form-data' in request.content_type:
        content = request.form.get('content', '').strip()
        parent_id = request.form.get('parent_id', type=int)
    else:
        content = request.form.get('content', '').strip()
        parent_id = request.form.get('parent_id', type=int)
    
    if not content:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400
        flash('Comment cannot be empty', 'danger')
        return redirect(url_for('community.community_home'))
    
    comment = Comment(
        content=content,
        user_id=current_user.id,
        post_id=post_id,
        parent_id=parent_id if parent_id else None,
        created_at=get_ph_time()
    )
    db.session.add(comment)
    
    # ========== NOTIFICATION FOR NEW COMMENT ==========
    if post.user_id != current_user.id:
        notification = Notification(
            user_id=post.user_id,
            title="💬 New Comment on Your Post",
            message=f"{current_user.name} commented: \"{content[:50]}...\"",
            notification_type='comment',
            related_id=post_id,
            related_type='post',
            icon="fas fa-comment",
            action_url=url_for('community.view_post', post_id=post_id),
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
    
    # Also notify parent comment author if replying
    if parent_id:
        parent_comment = Comment.query.get(parent_id)
        if parent_comment and parent_comment.user_id != current_user.id and parent_comment.user_id != post.user_id:
            reply_notification = Notification(
                user_id=parent_comment.user_id,
                title="↩️ New Reply to Your Comment",
                message=f"{current_user.name} replied to your comment: \"{content[:50]}...\"",
                notification_type='comment_reply',
                related_id=post_id,
                related_type='post',
                icon="fas fa-reply",
                action_url=url_for('community.view_post', post_id=post_id),
                created_at=datetime.utcnow()
            )
            db.session.add(reply_notification)
    # ========== END NOTIFICATION ==========
    
    db.session.commit()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True, 
            'message': 'Comment added!',
            'comment_id': comment.id
        })
    
    flash('Comment added!', 'success')
    return redirect(url_for('community.community_home'))

@community_bp.route('/api/comment/like/<int:comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
    existing_like = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()
    comment = Comment.query.get(comment_id)
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        like = CommentLike(user_id=current_user.id, comment_id=comment_id, created_at=get_ph_time())
        db.session.add(like)
        liked = True
        
        # ========== NOTIFICATION FOR COMMENT LIKE ==========
        if comment and comment.user_id != current_user.id:
            notification = Notification(
                user_id=comment.user_id,
                title="❤️ Someone Liked Your Comment",
                message=f"{current_user.name} liked your comment: \"{comment.content[:50]}...\"",
                notification_type='comment_like',
                related_id=comment_id,
                related_type='comment',
                icon="fas fa-heart",
                action_url=url_for('community.view_post', post_id=comment.post_id),
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
        # ========== END NOTIFICATION ==========
    
    db.session.commit()
    like_count = CommentLike.query.filter_by(comment_id=comment_id).count()
    return jsonify({'success': True, 'liked': liked, 'like_count': like_count})

@community_bp.route('/api/comment/edit/<int:comment_id>', methods=['POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'success': False, 'message': 'Content is required'}), 400
    comment.content = data['content'].strip()
    comment.updated_at = get_ph_time()
    db.session.commit()
    return jsonify({'success': True, 'message': 'Comment updated'})

@community_bp.route('/api/comment/delete/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    CommentLike.query.filter_by(comment_id=comment_id).delete()
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Comment deleted'})

@community_bp.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    if hasattr(post, 'increment_views'):
        post.increment_views()
    comment_form = CommentForm()
    
    # Add this to check if current user liked the post
    liked_posts = [like.post_id for like in PostLike.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('community/post_detail.html', 
                         post=post, 
                         comment_form=comment_form, 
                         title=post.title or 'Post',
                         liked_posts=liked_posts)

@community_bp.route('/create_post', methods=['POST'])
@login_required
def create_post():
    post_type = request.form.get('post_type', 'discussion')
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    topic_id = request.form.get('topic_id', 0, type=int)
    
    if not content:
        flash('Content is required', 'danger')
        return redirect(url_for('community.community_home'))
    
    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename:
            filename = secure_filename(file.filename)
            timestamp = get_ph_time().strftime("%Y%m%d_%H%M%S_")
            filename = timestamp + filename
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'post_images')
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            image_filename = filename
    
    post = Post(
        title=title if title else None,
        content=content,
        user_id=current_user.id,
        topic_id=topic_id if topic_id != 0 else None,
        post_type=post_type,
        media_file=image_filename,
        media_type='image' if image_filename else None,
        created_at=get_ph_time()
    )
    
    db.session.add(post)
    db.session.commit()
    
    # ========== NOTIFICATION FOR NEW POST (Optional: Notify admins or topic followers) ==========
    # Notify admin users about new post (optional)
    admins = User.query.filter_by(is_admin=True).all()
    for admin in admins:
        if admin.id != current_user.id:
            admin_notification = Notification(
                user_id=admin.id,
                title="📝 New Post Created",
                message=f"{current_user.name} created a new {post_type}: \"{title or content[:50]}...\"",
                notification_type='new_post',
                related_id=post.id,
                related_type='post',
                icon="fas fa-file-alt",
                action_url=url_for('community.view_post', post_id=post.id),
                created_at=datetime.utcnow()
            )
            db.session.add(admin_notification)
    
    # Notify followers (if you have a follow system - optional)
    # This would require a Follow model
    
    db.session.commit()
    # ========== END NOTIFICATION ==========
    
    flash('Post created successfully!', 'success')
    return redirect(url_for('community.community_home'))

# Discussion Rooms Routes
@community_bp.route('/discussion-rooms')
@login_required
def discussion_rooms():
    rooms = GroupChat.query.order_by(GroupChat.id.asc()).all()  # Changed to asc()
    if not rooms:
        create_default_discussion_rooms()
        rooms = GroupChat.query.order_by(GroupChat.id.asc()).all()
    for room in rooms:
        room.is_member = GroupMember.query.filter_by(group_id=room.id, user_id=current_user.id).first() is not None
        room.member_count = GroupMember.query.filter_by(group_id=room.id).count()
    return render_template('community/discussion_rooms.html', rooms=rooms, title='Discussion Rooms')

@community_bp.route('/discussion-room/<int:room_id>')
@login_required
def discussion_room(room_id):
    room = GroupChat.query.get_or_404(room_id)
    membership = GroupMember.query.filter_by(group_id=room.id, user_id=current_user.id).first()
    if not membership:
        membership = GroupMember(group_id=room.id, user_id=current_user.id, role='member')
        db.session.add(membership)
        room.member_count = (room.member_count or 0) + 1
        db.session.commit()
    messages = GroupMessage.query.filter_by(group_id=room.id).order_by(GroupMessage.created_at.asc()).all()
    for msg in messages:
        read_by = msg.get_read_by()
        if current_user.id not in read_by:
            read_by.append(current_user.id)
            msg.set_read_by(read_by)
    db.session.commit()
    other_rooms = GroupChat.query.filter(GroupChat.id != room.id).limit(5).all()
    for other in other_rooms:
        other.member_count = GroupMember.query.filter_by(group_id=other.id).count()
    return render_template('community/discussion_room.html', room=room, messages=messages, other_rooms=other_rooms, title=room.name)

@community_bp.route('/api/room/<int:room_id>/message', methods=['POST'])
@login_required
def send_room_message(room_id):
    room = GroupChat.query.get_or_404(room_id)
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'})
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'message': 'Message cannot be empty'})
    membership = GroupMember.query.filter_by(group_id=room.id, user_id=current_user.id).first()
    if not membership:
        membership = GroupMember(group_id=room.id, user_id=current_user.id, role='member')
        db.session.add(membership)
        room.member_count = (room.member_count or 0) + 1
    message = GroupMessage(content=content, sender_id=current_user.id, group_id=room.id, message_type='text', created_at=get_ph_time())
    db.session.add(message)
    room.last_message_at = get_ph_time()
    db.session.commit()
    return jsonify({'success': True, 'message': {'id': message.id, 'content': message.content, 'sender_id': current_user.id, 'sender_name': current_user.name, 'sender_avatar': current_user.get_avatar(), 'message_type': 'text', 'created_at': message.created_at.isoformat(), 'time_ago': time_ago(message.created_at)}})

@community_bp.route('/api/room/<int:room_id>/messages')
@login_required
def get_room_messages(room_id):
    room = GroupChat.query.get_or_404(room_id)
    after = request.args.get('after', type=int)
    query = GroupMessage.query.filter_by(group_id=room.id)
    if after:
        query = query.filter(GroupMessage.id > after)
    messages = query.order_by(GroupMessage.created_at.asc()).all()
    result = []
    for m in messages:
        msg_time = m.created_at
        if msg_time.tzinfo is None:
            msg_time = pytz.UTC.localize(msg_time)
        pht_time = msg_time.astimezone(PHT)
        result.append({'id': m.id, 'content': m.content, 'sender_id': m.sender_id, 'sender_name': m.sender.name, 'sender_avatar': m.sender.get_avatar(), 'message_type': m.message_type, 'file_path': m.file_path, 'file_name': m.file_name, 'file_size': m.file_size, 'created_at': pht_time.isoformat(), 'time_ago': time_ago(m.created_at), 'is_own': m.sender_id == current_user.id})
    return jsonify({'messages': result})

@community_bp.route('/api/room/<int:room_id>/upload', methods=['POST'])
@login_required
def upload_room_file(room_id):
    room = GroupChat.query.get_or_404(room_id)
    membership = GroupMember.query.filter_by(group_id=room.id, user_id=current_user.id).first()
    if not membership:
        membership = GroupMember(group_id=room.id, user_id=current_user.id, role='member')
        db.session.add(membership)
        room.member_count = (room.member_count or 0) + 1
        db.session.commit()
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf', 'doc', 'docx', 'txt'}
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'success': False, 'message': f'File type .{ext} not allowed'}), 400
    if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}:
        message_type = 'image'
    else:
        message_type = 'file'
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'group_messages')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, unique_filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    message = GroupMessage(content=filename, sender_id=current_user.id, group_id=room.id, message_type=message_type, file_path=unique_filename, file_name=filename, file_size=file_size, created_at=get_ph_time())
    db.session.add(message)
    room.last_message_at = get_ph_time()
    db.session.commit()
    return jsonify({'success': True, 'message': {'id': message.id, 'content': message.content, 'sender_id': current_user.id, 'sender_name': current_user.name, 'message_type': message.message_type, 'file_path': message.file_path, 'file_name': message.file_name, 'file_size': message.file_size, 'created_at': message.created_at.isoformat(), 'time_ago': time_ago(message.created_at)}})

def create_default_discussion_rooms():
    """Create the 9 default discussion rooms for AB Engineering Guild"""
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User.query.first()
    if not admin:
        return
    
    # ========== UPDATED: 9 DISCUSSION ROOMS ==========
    default_rooms = [
        {'name': 'AB Engineering Guild', 
         'description': 'Main hub for announcements, events, and general discussions for all ABE students'},
        
        {'name': 'Board Exam Q & A', 
         'description': 'Ask questions, share tips, and discuss board exam preparations with fellow reviewees'},
        
        {'name': 'Students Community', 
         'description': 'Casual conversations, study groups, and daily student life discussions'},
        
        {'name': 'Thesis and Research Help', 
         'description': 'Get help with research methodology, statistics, and thesis writing'},
        
        {'name': 'Career & Industry Connections', 
         'description': 'Job postings, internship opportunities, and career advice from ABE professionals'},
        
        {'name': 'Masters and Doctorate Discussion', 
         'description': 'For graduate students to discuss advanced topics, research, and grad school life'},
        
        {'name': 'Research & Innovation PH', 
         'description': 'Share and discuss agricultural innovations, research papers, and new technologies'},
        
        {'name': 'Bayaw Fun Stories', 
         'description': 'Relaxed off-topic chat for sharing fun stories, memes, and bonding'},
        
        {'name': 'ABE Trivia & Challenges', 
         'description': 'Daily trivia, quiz challenges, and friendly competitions about AB Engineering'},
    ]
    
    for room_data in default_rooms:
        existing = GroupChat.query.filter_by(name=room_data['name']).first()
        if not existing:
            room = GroupChat(
                name=room_data['name'], 
                description=room_data['description'], 
                owner_id=admin.id, 
                created_by=admin.id, 
                is_private=False, 
                created_at=get_ph_time(), 
                last_message_at=get_ph_time()
            )
            db.session.add(room)
    
    db.session.commit()
    print(f"[INFO] Created {len(default_rooms)} default discussion rooms")

@community_bp.route('/find-friends')
@login_required
def find_friends():
    query = request.args.get('q', '').strip()
    if query:
        users = User.query.filter(or_(User.name.ilike(f'%{query}%'), User.email.ilike(f'%{query}%')), User.id != current_user.id).limit(20).all()
    else:
        friend_ids = [f.id for f in current_user.get_friends()] + [current_user.id] if hasattr(current_user, 'get_friends') else [current_user.id]
        users = User.query.filter(~User.id.in_(friend_ids)).limit(20).all()
    for user in users:
        user.is_friend = current_user.is_friends_with(user) if hasattr(current_user, 'is_friends_with') else False
        user.has_pending_request = FriendRequest.query.filter(or_(and_(FriendRequest.sender_id == current_user.id, FriendRequest.receiver_id == user.id), and_(FriendRequest.sender_id == user.id, FriendRequest.receiver_id == current_user.id)), FriendRequest.status == 'pending').first() is not None
    return render_template('community/find_friends.html', users=users, query=query, title='Find Friends')

@community_bp.route('/post/<int:post_id>/edit', methods=['POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
    
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'message': 'Content cannot be empty'}), 400
    
    if title:
        post.title = title
    else:
        post.title = None
    
    post.content = content
    post.updated_at = get_ph_time()
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Post updated successfully',
        'post': {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'updated_at': post.updated_at.isoformat()
        }
    })

@community_bp.route('/api/send-request/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    """Send a connection request to another user"""
    receiver = User.query.get_or_404(user_id)
    
    if receiver.id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot send request to yourself'}), 400
    
    # Check if already friends
    if current_user.is_friends_with(receiver):
        return jsonify({'success': False, 'message': 'Already connected'}), 400
    
    # Check if request already exists
    existing_request = FriendRequest.query.filter(
        ((FriendRequest.sender_id == current_user.id) & (FriendRequest.receiver_id == receiver.id)) |
        ((FriendRequest.sender_id == receiver.id) & (FriendRequest.receiver_id == current_user.id))
    ).first()
    
    if existing_request:
        if existing_request.status == 'pending':
            return jsonify({'success': False, 'message': 'Request already pending'}), 400
        elif existing_request.status == 'accepted':
            return jsonify({'success': False, 'message': 'Already connected'}), 400
    
    # Create friend request
    request = FriendRequest(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        status='pending',
        created_at=datetime.utcnow()
    )
    
    db.session.add(request)
    
    # Create notification for receiver
    notification = Notification(
        user_id=receiver.id,
        title='👋 New Connection Request',
        message=f'{current_user.name} wants to connect with you',
        notification_type='friend_request',
        related_id=request.id,
        action_url=url_for('community.friend_requests'),
        icon='fas fa-user-plus',
        created_at=datetime.utcnow()
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Connection request sent!'})

@community_bp.route('/api/accept-request/<int:request_id>', methods=['POST'])
@login_required
def accept_friend_request(request_id):
    """Accept a friend request"""
    request = FriendRequest.query.get_or_404(request_id)
    
    if request.receiver_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if request.status != 'pending':
        return jsonify({'success': False, 'message': 'Request already processed'}), 400
    
    # Update request status
    request.status = 'accepted'
    
    # Create friendship record
    friendship1 = Friendship(
        user_id=request.sender_id,
        friend_id=request.receiver_id,
        status='accepted',
        created_at=datetime.utcnow()
    )
    friendship2 = Friendship(
        user_id=request.receiver_id,
        friend_id=request.sender_id,
        status='accepted',
        created_at=datetime.utcnow()
    )
    
    db.session.add(friendship1)
    db.session.add(friendship2)
    
    # Create notification for sender
    notification = Notification(
        user_id=request.sender_id,
        title='🤝 Connection Accepted',
        message=f'{current_user.name} accepted your connection request',
        notification_type='friend_request_accepted',
        related_id=request.id,
        action_url=url_for('messages.start_conversation', user_id=current_user.id),
        icon='fas fa-handshake',
        created_at=datetime.utcnow()
    )
    db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Connection accepted!'})

@community_bp.route('/api/decline-request/<int:request_id>', methods=['POST'])
@login_required
def decline_friend_request(request_id):
    """Decline a friend request"""
    request = FriendRequest.query.get_or_404(request_id)
    
    if request.receiver_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    if request.status != 'pending':
        return jsonify({'success': False, 'message': 'Request already processed'}), 400
    
    # Update request status
    request.status = 'rejected'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Request declined'})

@community_bp.route('/api/cancel-request/<int:user_id>', methods=['POST'])
@login_required
def cancel_friend_request(user_id):
    """Cancel a sent friend request"""
    receiver = User.query.get_or_404(user_id)
    
    request = FriendRequest.query.filter(
        FriendRequest.sender_id == current_user.id,
        FriendRequest.receiver_id == receiver.id,
        FriendRequest.status == 'pending'
    ).first()
    
    if not request:
        return jsonify({'success': False, 'message': 'No pending request found'}), 404
    
    db.session.delete(request)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Request cancelled'})

@community_bp.route('/friend-requests')
@login_required
def friend_requests():
    """View all friend requests"""
    received_requests = FriendRequest.query.filter_by(
        receiver_id=current_user.id,
        status='pending'
    ).order_by(FriendRequest.created_at.desc()).all()
    
    sent_requests = FriendRequest.query.filter_by(
        sender_id=current_user.id,
        status='pending'
    ).order_by(FriendRequest.created_at.desc()).all()
    
    return render_template('community/friend_requests.html',
                         received_requests=received_requests,
                         sent_requests=sent_requests,
                         title='Friend Requests')

@community_bp.route('/api/message/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_group_message(message_id):
    """Edit a group message (only within 5 minutes)"""
    message = GroupMessage.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    time_diff = datetime.utcnow() - message.created_at
    if time_diff.total_seconds() > 300:
        return jsonify({'success': False, 'message': 'Messages can only be edited within 5 minutes'}), 400
    
    data = request.get_json()
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return jsonify({'success': False, 'message': 'Content cannot be empty'}), 400
    
    message.content = new_content
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Message updated'})


@community_bp.route('/api/message/<int:message_id>/delete', methods=['DELETE'])
@login_required
def delete_group_message(message_id):
    """Delete a group message"""
    message = GroupMessage.query.get_or_404(message_id)
    
    if message.sender_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(message)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Message deleted'})