# app/models.py - COMPLETE CLEAN VERSION (FIXED)
from app import db, login_manager
from flask_login import UserMixin
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import secrets
import hashlib


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reset_token = db.Column(db.String(100), nullable=True, unique=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    recovery_key_hash = db.Column(db.String(128), nullable=True)
    
    profile_picture = db.Column(db.String(255), nullable=True, default='default_profile.png')
    cover_photo = db.Column(db.String(255), nullable=True, default='default_cover.jpg')
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    notification_preferences = db.Column(db.Text, default='{}')
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    
    # Friends relationships
    friends = db.relationship('Friendship', 
                            foreign_keys='Friendship.user_id',
                            backref='user', lazy=True)
    friend_of = db.relationship('Friendship',
                              foreign_keys='Friendship.friend_id',
                              backref='friend', lazy=True)
    
    # Messages relationships
    sent_messages = db.relationship('Message', 
                                  foreign_keys='Message.sender_id',
                                  backref='sender', lazy=True)
    received_messages = db.relationship('Message', 
                                      foreign_keys='Message.receiver_id', 
                                      backref='receiver', lazy=True)
    
    # Sent and received friend requests
    sent_friend_requests = db.relationship('FriendRequest', 
                                         foreign_keys='FriendRequest.sender_id', 
                                         backref='sender', lazy=True)
    received_friend_requests = db.relationship('FriendRequest', 
                                             foreign_keys='FriendRequest.receiver_id', 
                                             backref='receiver', lazy=True)
    
    # Study plans and goals
    study_plans = db.relationship('StudyPlan', backref='user', lazy=True)
    learning_goals = db.relationship('LearningGoal', backref='user', lazy=True)
    
    # Posts and comments relationships
    posts = db.relationship('Post', backref='author', lazy=True, foreign_keys='Post.user_id')
    comments = db.relationship('Comment', backref='author', lazy=True, foreign_keys='Comment.user_id')
    post_likes = db.relationship('PostLike', backref='user', lazy=True, foreign_keys='PostLike.user_id')
    comment_likes = db.relationship('CommentLike', backref='user', lazy=True, foreign_keys='CommentLike.user_id')
    post_shares = db.relationship('PostShare', backref='user', lazy=True, foreign_keys='PostShare.user_id')
    
    # Conversations
    conversations_as_user1 = db.relationship('Conversation', 
                                           foreign_keys='Conversation.user1_id', 
                                           backref='user1', lazy=True)
    conversations_as_user2 = db.relationship('Conversation', 
                                           foreign_keys='Conversation.user2_id', 
                                           backref='user2', lazy=True)
    
    # Group chat memberships
    group_memberships = db.relationship('GroupMember', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # ========== PASSWORD RESET METHODS ==========
    def generate_reset_token(self):
        """Generate a secure password reset token"""
        raw_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        self.reset_token = hashed_token
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return raw_token
    
    def verify_reset_token(self, token):
        """Verify if the reset token is valid"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        
        hashed_token = hashlib.sha256(token.encode()).hexdigest()
        if self.reset_token != hashed_token:
            return False
        
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        
        return True
    
    def clear_reset_token(self):
        """Clear the reset token after use"""
        self.reset_token = None
        self.reset_token_expiry = None
    # ========== END PASSWORD RESET METHODS ==========

    # ========== RECOVERY KEY METHODS ==========
    def generate_recovery_key(self):
        """Generate a unique recovery key for the user"""
        parts = []
        for _ in range(3):
            part = secrets.token_urlsafe(4).upper().replace('-', '').replace('_', '')
            parts.append(part)
        recovery_key = f"ABE-{parts[0]}-{parts[1]}-{parts[2]}"
        
        hashed_key = hashlib.sha256(recovery_key.encode()).hexdigest()
        self.recovery_key_hash = hashed_key
        return recovery_key

    def verify_recovery_key(self, key):
        """Verify if the recovery key is correct"""
        if not self.recovery_key_hash:
            return False
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return self.recovery_key_hash == hashed_key
    # ========== END RECOVERY KEY METHODS ==========
    
    def get_avatar(self):
        if self.profile_picture and self.profile_picture not in ['default_profile.png', 'default.jpg']:
            return url_for('static', filename=f'uploads/profile_pictures/{self.profile_picture}')
        initials = self.name[0].upper() if self.name else 'U'
        return f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 40 40'%3E%3Ccircle cx='20' cy='20' r='20' fill='%2322c55e'/%3E%3Ctext x='20' y='28' text-anchor='middle' fill='white' font-size='18' font-weight='bold'%3E{initials}%3C/text%3E%3C/svg%3E"
    
    def is_friends_with(self, user):
        return Friendship.query.filter(
            ((Friendship.user_id == self.id) & (Friendship.friend_id == user.id)) |
            ((Friendship.user_id == user.id) & (Friendship.friend_id == self.id))
        ).filter(Friendship.status == 'accepted').first() is not None
    
    def get_friend_request(self, user):
        return FriendRequest.query.filter(
            ((FriendRequest.sender_id == self.id) & (FriendRequest.receiver_id == user.id)) |
            ((FriendRequest.sender_id == user.id) & (FriendRequest.receiver_id == self.id))
        ).first()
    
    def get_pending_friend_requests(self):
        return FriendRequest.query.filter_by(receiver_id=self.id, status='pending').all()
    
    def get_friends(self):
        friendships = Friendship.query.filter(
            ((Friendship.user_id == self.id) | (Friendship.friend_id == self.id)) &
            (Friendship.status == 'accepted')
        ).all()
        
        friends = []
        for friendship in friendships:
            if friendship.user_id == self.id:
                friends.append(friendship.friend)
            else:
                friends.append(friendship.user)
        return friends
    
    def get_unread_notifications_count(self):
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()
    
    def get_recent_notifications(self, limit=5):
        return Notification.query.filter_by(user_id=self.id).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()
    
    def get_notification_preferences(self):
        return json.loads(self.notification_preferences)
    
    def set_notification_preferences(self, preferences):
        self.notification_preferences = json.dumps(preferences)
    
    def should_receive_notification(self, notification_type):
        prefs = self.get_notification_preferences()
        return prefs.get(notification_type, True)
    
    @property
    def followers_count(self):
        return Friendship.query.filter_by(friend_id=self.id, status='accepted').count()

    @property
    def following_count(self):
        return Friendship.query.filter_by(user_id=self.id, status='accepted').count()

    @property
    def friends_count(self):
        return len(self.get_friends())
    
    def has_hidden_post(self, post_id):
        return HiddenPost.query.filter_by(user_id=self.id, post_id=post_id).first() is not None

    def has_saved_post(self, post_id):
        return SavedPost.query.filter_by(user_id=self.id, post_id=post_id).first() is not None

    def has_snoozed_post(self, post_id):
        return SnoozedPost.query.filter_by(user_id=self.id, post_id=post_id).first() is not None

    def get_post_interest(self, post_id):
        return PostInterest.query.filter_by(user_id=self.id, post_id=post_id).first()

    def is_online(self):
        if self.last_seen:
            return (datetime.utcnow() - self.last_seen).total_seconds() < 300
        return False
    
    def __repr__(self):
        return f'<User {self.name}>'


class Conversation(db.Model):
    __tablename__ = 'conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_other_user(self, current_user_id):
        return self.user2 if self.user1_id == current_user_id else self.user1
    
    def get_unread_count(self, user_id):
        return self.messages.filter(
            Message.receiver_id == user_id,
            Message.is_read == False
        ).count()
    
    def get_last_message(self):
        return self.messages.order_by(Message.created_at.desc()).first()
    
    def __repr__(self):
        return f'<Conversation {self.user1_id} - {self.user2_id}>'


class Message(db.Model):
    __tablename__ = 'message'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    message_type = db.Column(db.String(20), default='text')
    file_path = db.Column(db.String(500))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    thumbnail_path = db.Column(db.String(500))
    duration = db.Column(db.Integer)
    call_type = db.Column(db.String(20))
    call_duration = db.Column(db.Integer)
    call_status = db.Column(db.String(20))
    reply_to_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_edited = db.Column(db.Boolean, default=False)
    
    replied_message = db.relationship('Message', remote_side=[id], backref='replies')
    reactions = db.relationship('MessageReaction', backref='message', lazy=True)
    
    def __repr__(self):
        return f'<Message {self.id}>'


class MessageReaction(db.Model):
    __tablename__ = 'message_reaction'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reaction = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MessageReaction {self.user_id} - {self.reaction}>'


class CallSession(db.Model):
    __tablename__ = 'call_session'
    
    id = db.Column(db.Integer, primary_key=True)
    caller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    call_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='ringing')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    
    caller = db.relationship('User', foreign_keys=[caller_id], backref='caller_sessions')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='receiver_sessions')
    
    def __repr__(self):
        return f'<CallSession {self.caller_id} -> {self.receiver_id}>'


class FriendRequest(db.Model):
    __tablename__ = 'friend_request'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<FriendRequest {self.sender_id} -> {self.receiver_id}>'


class Friendship(db.Model):
    __tablename__ = 'friendship'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Friendship {self.user_id} - {self.friend_id}>'


class Topic(db.Model):
    __tablename__ = 'topic'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fas fa-folder')
    color = db.Column(db.String(7), default='#4CAF50')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    questions = db.relationship('Question', backref='topic', lazy=True)
    materials = db.relationship('StudyMaterial', backref='topic', lazy=True)
    quiz_results = db.relationship('QuizResult', backref='topic', lazy=True)
    posts = db.relationship('Post', backref='topic', lazy=True)
    
    def __repr__(self):
        return f'<Topic {self.name}>'


class Post(db.Model):
    __tablename__ = 'post'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    post_type = db.Column(db.String(20), default='discussion')
    media_file = db.Column(db.String(255))
    media_type = db.Column(db.String(20))
    view_count = db.Column(db.Integer, default=0)
    parent_post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    answers = db.relationship('Post', 
                            backref=db.backref('parent_post', remote_side=[id]),
                            lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship('PostLike', backref='post', lazy=True)
    shares = db.relationship('PostShare', backref='post', lazy=True)
    
    def like_count(self):
        return PostLike.query.filter_by(post_id=self.id).count()
    
    def comment_count(self):
        return Comment.query.filter_by(post_id=self.id).count()
    
    def answer_count(self):
        return Post.query.filter_by(parent_post_id=self.id, post_type='answer').count()
    
    def share_count(self):
        return PostShare.query.filter_by(post_id=self.id).count()
    
    def increment_views(self):
        self.view_count += 1
        db.session.commit()
    
    def get_users_who_liked(self):
        return [like.user for like in self.likes]
    
    def get_users_who_shared(self):
        return [share.user for share in self.shares]
    
    def __repr__(self):
        return f'<Post {self.id} by {self.user_id}>'


class PostLike(db.Model):
    __tablename__ = 'post_like'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostLike {self.user_id} - {self.post_id}>'


class PostShare(db.Model):
    __tablename__ = 'post_share'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    shared_to = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostShare {self.user_id} - {self.post_id}>'


class Comment(db.Model):
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    replies = db.relationship('Comment', 
                            backref=db.backref('parent', remote_side=[id]),
                            lazy=True)
    likes = db.relationship('CommentLike', backref='comment', lazy=True)
    
    def like_count(self):
        return CommentLike.query.filter_by(comment_id=self.id).count()
    
    def __repr__(self):
        return f'<Comment {self.id} by {self.user_id}>'


class CommentLike(db.Model):
    __tablename__ = 'comment_like'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CommentLike {self.user_id} - {self.comment_id}>'


class Notification(db.Model):
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    related_id = db.Column(db.Integer)
    related_type = db.Column(db.String(50))
    action_url = db.Column(db.String(500))
    icon = db.Column(db.String(100), default='fas fa-bell')
    priority = db.Column(db.String(20), default='normal')
    is_read = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.notification_type,
            'icon': self.icon,
            'priority': self.priority,
            'is_read': self.is_read,
            'action_url': self.action_url,
            'created_at': self.created_at.isoformat(),
            'time_ago': self.get_time_ago()
        }
    
    def get_time_ago(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    
    def __repr__(self):
        return f'<Notification {self.id} for {self.user_id}>'


class Question(db.Model):
    __tablename__ = 'question'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Question {self.id}>'


class StudyMaterial(db.Model):
    __tablename__ = 'study_material'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    file_path = db.Column(db.String(300))
    material_type = db.Column(db.String(50), default='pdf')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyMaterial {self.title}>'


class QuizResult(db.Model):
    __tablename__ = 'quiz_result'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    time_taken = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ONLY ADD THE USER RELATIONSHIP HERE
    # The topic relationship is already defined in the Topic model with backref
    user = db.relationship('User', backref='quiz_results', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<QuizResult {self.user_id} - {self.score}>'


class PAESStandard(db.Model):
    __tablename__ = 'paes_standard'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(300))
    category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PAESStandard {self.code}>'


class HiddenPost(db.Model):
    __tablename__ = 'hidden_post'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<HiddenPost {self.user_id} - {self.post_id}>'


class SavedPost(db.Model):
    __tablename__ = 'saved_post'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    folder = db.Column(db.String(100), default='general')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SavedPost {self.user_id} - {self.post_id}>'


class PostInterest(db.Model):
    __tablename__ = 'post_interest'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    interest_type = db.Column(db.String(20), default='interested')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostInterest {self.user_id} - {self.post_id}>'


class SnoozedPost(db.Model):
    __tablename__ = 'snoozed_post'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    snooze_until = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SnoozedPost {self.user_id} - {self.post_id}>'


class Achievement(db.Model):
    __tablename__ = 'achievement'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100), default='fas fa-trophy')
    points = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), default='general')  # quiz, streak, social, mastery, special
    requirement_type = db.Column(db.String(50), default='quiz_count')  # quiz_count, score, streak, topic_mastery, etc.
    requirement_value = db.Column(db.Integer, default=0)
    requirement_extra = db.Column(db.String(100), nullable=True)  # For topic-specific or additional params
    badge_color = db.Column(db.String(20), default='yellow')  # yellow, green, blue, purple, red, indigo
    display_order = db.Column(db.Integer, default=0)
    is_hidden = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    users = db.relationship('UserAchievement', backref='achievement', lazy=True)
    
    def __repr__(self):
        return f'<Achievement {self.name}>'
    
    def get_badge_color_class(self):
        colors = {
            'yellow': 'bg-yellow-500',
            'green': 'bg-green-500',
            'blue': 'bg-blue-500',
            'purple': 'bg-purple-500',
            'red': 'bg-red-500',
            'indigo': 'bg-indigo-500',
            'pink': 'bg-pink-500',
            'orange': 'bg-orange-500'
        }
        return colors.get(self.badge_color, 'bg-yellow-500')
    
    def get_icon_html(self):
        return f'<i class="{self.icon} text-2xl"></i>'


class UserAchievement(db.Model):
    __tablename__ = 'user_achievement'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    progress = db.Column(db.Float, default=0.0)  # Progress percentage (0-100)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='user_achievements')
    
    def __repr__(self):
        return f'<UserAchievement {self.user_id} - {self.achievement_id}>'


class StudyPlan(db.Model):
    __tablename__ = 'study_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    topics = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<StudyPlan {self.title}>'


class LearningGoal(db.Model):
    __tablename__ = 'learning_goal'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    target_date = db.Column(db.DateTime)
    progress = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LearningGoal {self.title}>'


class GroupChat(db.Model):
    __tablename__ = 'group_chat'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100), default='fas fa-users')
    cover_photo = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    member_count = db.Column(db.Integer, default=1)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    owner = db.relationship('User', foreign_keys=[owner_id], backref='owned_groups')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_groups')
    members = db.relationship('GroupMember', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    messages = db.relationship('GroupMessage', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_last_message(self):
        return self.messages.order_by(GroupMessage.created_at.desc()).first()
    
    def get_unread_count(self, user_id):
        unread = 0
        for msg in self.messages.filter(GroupMessage.created_at > datetime.utcnow() - timedelta(days=7)).all():
            if msg.read_by is None or user_id not in msg.read_by:
                unread += 1
        return unread
    
    def __repr__(self):
        return f'<GroupChat {self.name}>'


class GroupMember(db.Model):
    __tablename__ = 'group_member'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_read_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<GroupMember {self.user_id} in {self.group_id}>'


class GroupMessage(db.Model):
    __tablename__ = 'group_message'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group_chat.id'), nullable=False)
    message_type = db.Column(db.String(20), default='text')
    file_path = db.Column(db.String(500))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    thumbnail_path = db.Column(db.String(500))
    read_by = db.Column(db.Text, default='[]')
    reply_to_id = db.Column(db.Integer, db.ForeignKey('group_message.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship('User', backref='group_messages')
    replies = db.relationship('GroupMessage', remote_side=[id])
    
    def get_read_by(self):
        return json.loads(self.read_by) if self.read_by else []
    
    def set_read_by(self, user_ids):
        self.read_by = json.dumps(user_ids)
    
    def __repr__(self):
        return f'<GroupMessage {self.id} in {self.group_id}>'


class Note(db.Model):
    __tablename__ = 'note'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    color = db.Column(db.String(50), default='bg-yellow-100')
    border_color = db.Column(db.String(50), default='border-yellow-300')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='notes')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'color': self.color,
            'borderColor': self.border_color,
            'createdAt': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Note {self.id} - {self.title}>'

class MaterialLink(db.Model):
    """Store external links for study materials (Review Materials & Videos)"""
    __tablename__ = 'material_link'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, nullable=False, default=0)  # <-- MAKE SURE THIS LINE EXISTS
    topic_name = db.Column(db.String(100), nullable=False)
    material_title = db.Column(db.String(300), nullable=False)
    link_name = db.Column(db.String(100), nullable=False)
    link_url = db.Column(db.String(500), nullable=False)
    link_type = db.Column(db.String(50), default='google_drive')
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MaterialLink {self.topic_name} - {self.material_title} - {self.link_name}>'


class ABELELink(db.Model):
    """Store ABELE Review Materials links (the 6 buttons)"""
    __tablename__ = 'abele_link'
    
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(100), nullable=False, unique=True)  # AREA I QUIZ, AREA I SOLVINGS, etc.
    title = db.Column(db.String(200), nullable=False)
    link_url = db.Column(db.String(500), nullable=False)
    icon = db.Column(db.String(50), default='fas fa-external-link-alt')
    color = db.Column(db.String(50), default='green')  # green, blue, purple
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ABELELink {self.section_name}>'

class UserPreference(db.Model):
    __tablename__ = 'user_preference'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    theme = db.Column(db.String(20), default='light')
    email_notifications = db.Column(db.Boolean, default=True)
    quiz_reminders = db.Column(db.Boolean, default=True)
    rank_notifications = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='preferences')
    
    def __repr__(self):
        return f'<UserPreference user_id={self.user_id}>'
    
# ========== THIS MUST BE AT THE VERY BOTTOM ==========
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add this class to app/models.py before the @login_manager.user_loader

class Announcement(db.Model):
    __tablename__ = 'announcement'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New attachment fields
    attachment_file = db.Column(db.String(500), nullable=True)  # File path
    attachment_filename = db.Column(db.String(255), nullable=True)  # Original filename
    attachment_size = db.Column(db.Integer, nullable=True)  # File size in bytes
    attachment_type = db.Column(db.String(50), nullable=True)  # image, pdf, document
    
    # Multiple images support (store as JSON array)
    images = db.Column(db.Text, nullable=True)  # JSON array of image paths
    
    # Relationships
    author = db.relationship('User', backref='announcements')
    
    def __repr__(self):
        return f'<Announcement {self.title}>'
    
    def get_time_ago(self):
        now = datetime.utcnow()
        diff = now - self.created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
        else:
            return "Just now"
    
    def get_images_list(self):
        """Return list of image paths"""
        if self.images:
            import json
            return json.loads(self.images)
        return []
    
    def get_file_icon(self):
        """Return icon class based on file type"""
        if not self.attachment_type:
            return 'fas fa-file'
        
        if self.attachment_type == 'image':
            return 'fas fa-image'
        elif self.attachment_type == 'pdf':
            return 'fas fa-file-pdf'
        elif self.attachment_type in ['doc', 'docx']:
            return 'fas fa-file-word'
        elif self.attachment_type in ['xls', 'xlsx']:
            return 'fas fa-file-excel'
        else:
            return 'fas fa-file'
    
    def get_file_size_display(self):
        """Return human readable file size"""
        if not self.attachment_size:
            return ''
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.attachment_size < 1024.0:
                return f"{self.attachment_size:.1f} {unit}"
            self.attachment_size /= 1024.0
        return f"{self.attachment_size:.1f} GB"

class StudyReminder(db.Model):
    __tablename__ = 'study_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Removed ForeignKey temporarily
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    completed = db.Column(db.Boolean, default=False)
    snoozed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'date': self.date,
            'time': self.time,
            'title': self.title,
            'topic': self.topic,
            'completed': self.completed,
            'snoozed': self.snoozed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }