# app/__init__.py - COMPLETE CORRECTED VERSION WITH ACHIEVEMENTS
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
import os
from pathlib import Path
from datetime import datetime

# Initialize extensions (these will be configured with app later)
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()
csrf = CSRFProtect()
socketio = SocketIO()

def get_database_uri():
    """Get the correct database URI with proper path handling"""
    env_uri = os.environ.get('DATABASE_URI')
    if env_uri:
        return env_uri
    
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'data' / 'quizzes.db'
    db_path.parent.mkdir(exist_ok=True)
    
    return f'sqlite:///{db_path}'

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    
    print(f"[DB] Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    try:
        from app.auth.routes import auth_bp
        app.register_blueprint(auth_bp)
        print("✓ Auth blueprint registered")
    except Exception as e:
        print(f"⚠ Auth blueprint error: {e}")
    
    try:
        from app.main.routes import main_bp
        app.register_blueprint(main_bp)
        print("✓ Main blueprint registered")
    except Exception as e:
        print(f"⚠ Main blueprint error: {e}")
    
    try:
        from app.reviewer.routes import reviewer_bp
        app.register_blueprint(reviewer_bp, url_prefix='/reviewer')
        print("✓ Reviewer blueprint registered")
    except Exception as e:
        print(f"⚠ Reviewer blueprint error: {e}")
    
    try:
        from app.quiz.routes import quiz_bp
        app.register_blueprint(quiz_bp, url_prefix='/quiz')
        print("✓ Quiz blueprint registered")
    except Exception as e:
        print(f"⚠ Quiz blueprint error: {e}")
    
    try:
        from app.scoreboard.routes import scoreboard_bp
        app.register_blueprint(scoreboard_bp, url_prefix='/scoreboard')
        print("✓ Scoreboard blueprint registered")
    except Exception as e:
        print(f"⚠ Scoreboard blueprint error: {e}")
    
    try:
        from app.admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
        print("✓ Admin blueprint registered")
    except Exception as e:
        print(f"⚠ Admin blueprint error: {e}")
    
    try:
        from app.community import community_bp
        app.register_blueprint(community_bp)
        print("✓ Community blueprint registered")
    except Exception as e:
        print(f"⚠ Community blueprint error: {e}")
    
    try:
        from app.profile.routes import profile_bp
        app.register_blueprint(profile_bp, url_prefix='/profile')
        print("✓ Profile blueprint registered")
    except Exception as e:
        print(f"⚠ Profile blueprint error: {e}")
    
    try:
        from app.messages.routes import messages_bp
        app.register_blueprint(messages_bp, url_prefix='/messages')
        print("✓ Messages blueprint registered")
    except Exception as e:
        print(f"⚠ Messages blueprint error: {e}")
    
    # Register Achievements blueprint
    try:
        from app.achievements import achievements_bp
        app.register_blueprint(achievements_bp, url_prefix='/achievements')
        print("✓ Achievements blueprint registered")
    except Exception as e:
        print(f"⚠ Achievements blueprint error: {e}")
    
    # Register socket events
    register_socket_events()
    
    # Context processor for notifications and messages
    @app.context_processor
    def inject_global_vars():
        from flask_login import current_user
        
        vars_dict = {
            'unread_notifications_count': 0,
            'unread_messages_count': 0
        }
        
        if current_user.is_authenticated:
            try:
                from app.models import Notification, Message
                
                unread_notifications = Notification.query.filter_by(
                    user_id=current_user.id, 
                    is_read=False
                ).count()
                vars_dict['unread_notifications_count'] = unread_notifications
                
                unread_messages = Message.query.filter_by(
                    receiver_id=current_user.id,
                    is_read=False
                ).count()
                vars_dict['unread_messages_count'] = unread_messages
                
            except Exception as e:
                print(f"⚠ Context processor error: {e}")
        
        return vars_dict
    
    # Create upload directories
    with app.app_context():
        try:
            upload_dirs = ['profile_pictures', 'cover_photos', 'post_images', 'messages']
            for dir_name in upload_dirs:
                dir_path = os.path.join(app.config['UPLOAD_FOLDER'], dir_name)
                os.makedirs(dir_path, exist_ok=True)
            print("✓ Upload directories created")
        except Exception as e:
            print(f"⚠ Upload directory creation failed: {e}")
    
    # Template filter
    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        if not dt:
            return "Never"
        
        now = datetime.utcnow()
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365}y ago"
        elif diff.days > 30:
            return f"{diff.days // 30}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    print("✅ Application initialized successfully!")
    return app

def register_socket_events():
    """Register Socket.IO event handlers"""
    from app import socketio
    from flask_socketio import emit, join_room, leave_room
    from flask_login import current_user
    
    @socketio.on('connect')
    def handle_connect():
        from flask import request
        print(f"Client connected: {request.sid}")
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            join_room(f'user_{current_user.id}')
            emit('connected', {'status': 'connected', 'user_id': current_user.id})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        from flask import request
        print(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_conversation')
    def handle_join_conversation(data):
        conversation_id = data.get('conversation_id')
        if conversation_id and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            room = f'conversation_{conversation_id}'
            join_room(room)
            print(f"User {current_user.id} joined conversation {conversation_id}")
    
    @socketio.on('leave_conversation')
    def handle_leave_conversation(data):
        conversation_id = data.get('conversation_id')
        if conversation_id:
            room = f'conversation_{conversation_id}'
            leave_room(room)
    
    @socketio.on('typing')
    def handle_typing(data):
        conversation_id = data.get('conversation_id')
        is_typing = data.get('is_typing', False)
        if conversation_id and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            emit('user_typing', {
                'conversation_id': conversation_id,
                'user_id': current_user.id,
                'user_name': current_user.name,
                'is_typing': is_typing
            }, room=f'conversation_{conversation_id}')