# app/main/routes.py - COMPLETE CLEAN VERSION
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, QuizResult, Topic, Notification, Announcement, Note, StudyReminder
from app.main import main_bp
from datetime import datetime, timedelta, date
from app import db
from sqlalchemy import func, desc
from werkzeug.utils import secure_filename
import json
import os

@main_bp.route('/api/ping', methods=['GET'])
def api_ping():
    return jsonify({'status': 'ok', 'message': 'Main blueprint is working!'})


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='AgriQuest')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # ========== CHECK ACHIEVEMENTS ON DASHBOARD LOAD ==========
    try:
        from app.achievements.routes import check_achievements
        check_achievements()
        print("DEBUG - Achievements checked on dashboard load")
    except Exception as e:
        print(f"DEBUG - Dashboard achievement check error: {e}")
    # ========== END ACHIEVEMENT CHECK ==========
    
    # Get user's recent quiz results (last 10 for activity feed)
    recent_quiz_results = QuizResult.query.filter_by(user_id=current_user.id)\
    .order_by(QuizResult.completed_at.desc()).limit(10).all()
    
    # Calculate stats
    total_quizzes = QuizResult.query.filter_by(user_id=current_user.id).count()
    
    if total_quizzes > 0:
        avg = db.session.query(func.avg(QuizResult.score))\
            .filter(QuizResult.user_id == current_user.id).scalar()
        average_score = round(avg, 2) if avg is not None else 0
    else:
        average_score = 0
    
    # Calculate attempts today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    attempts_today = QuizResult.query.filter(
        QuizResult.user_id == current_user.id,
        QuizResult.completed_at >= today_start
    ).count()

    # Calculate Streak
    all_results_dates = db.session.query(
        func.date(QuizResult.completed_at).label('quiz_date')
    ).filter(
        QuizResult.user_id == current_user.id,
        QuizResult.completed_at.isnot(None)
    ).group_by(
        func.date(QuizResult.completed_at)
    ).order_by(
        desc('quiz_date')
    ).all()

    quiz_dates = set(r.quiz_date for r in all_results_dates if r.quiz_date is not None)

    streak = 0
    today_local = date.today()
    current_date = today_local if today_local in quiz_dates else (today_local - timedelta(days=1))

    while current_date in quiz_dates:
        streak += 1
        current_date -= timedelta(days=1)

    # Get user's rank
    user_rank = "N/A"
    if total_quizzes > 0:
        subq = db.session.query(
            QuizResult.user_id,
            func.avg(QuizResult.score).label('avg_score')
        ).group_by(QuizResult.user_id).subquery()

        ranked_users = db.session.query(
            User.id,
            User.name,
            subq.c.avg_score,
            func.rank().over(order_by=desc(subq.c.avg_score)).label('rank')
        ).outerjoin(subq, User.id == subq.c.user_id).order_by(desc(subq.c.avg_score)).all()

        for u in ranked_users:
            if u.id == current_user.id:
                try:
                    user_rank = int(u.rank)
                except Exception:
                    user_rank = u.rank
                break
        else:
            user_rank = "Unranked"
    else:
        user_rank = "Unranked"

    # Get all topics for Topic Mastery
    topics = Topic.query.all()
    
    # Calculate average score for each topic
    topic_scores = []
    for topic in topics:
        topic_results = QuizResult.query.filter_by(
            user_id=current_user.id,
            topic_id=topic.id
        ).all()
        
        if topic_results:
            total_score = sum((result.score or 0) for result in topic_results)
            avg_score = round(total_score / len(topic_results), 2)
            
            if avg_score >= 91:
                rating = "Excellent"
                color = "bg-blue-600"
            elif avg_score >= 81:
                rating = "Very Good"
                color = "bg-purple-500"
            elif avg_score >= 51:
                rating = "Good"
                color = "bg-green-500"
            elif avg_score >= 31:
                rating = "Fair"
                color = "bg-yellow-500"
            else:
                rating = "Poor"
                color = "bg-red-500"
        else:
            avg_score = 0
            rating = "No data"
            color = "bg-gray-300"
            
        topic_scores.append({
            'topic': topic,
            'score': avg_score,
            'rating': rating,
            'color': color
        })

    # Chart data
    seven_days_ago = datetime.utcnow().date() - timedelta(days=6)
    all_days = [(seven_days_ago + timedelta(days=i)) for i in range(7)]
    day_labels = [day.strftime('%m/%d') for day in all_days]
    
    daily_scores_query = db.session.query(
        func.date(QuizResult.completed_at).label('date'),
        func.avg(QuizResult.score).label('avg_score')
    ).filter(
        QuizResult.user_id == current_user.id,
        QuizResult.completed_at.isnot(None),
        func.date(QuizResult.completed_at) >= seven_days_ago
    ).group_by(
        func.date(QuizResult.completed_at)
    ).order_by(
        func.date(QuizResult.completed_at)
    ).all()
    
    daily_scores_dict = {}
    for result in daily_scores_query:
        daily_scores_dict[str(result.date)] = round(float(result.avg_score), 2)
    
    daily_averages = []
    for day in all_days:
        day_str = str(day)
        if day_str in daily_scores_dict:
            daily_averages.append(daily_scores_dict[day_str])
        else:
            daily_averages.append(0)

    return render_template(
        'dashboard.html',
        title='Dashboard',
        quiz_results=recent_quiz_results,
        total_quizzes=total_quizzes,
        average_score=average_score,
        attempts_today=attempts_today,
        streak=streak,
        user_rank=user_rank,
        topics=topics,
        topic_scores=topic_scores,
        daily_labels=json.dumps(day_labels),
        daily_averages=json.dumps(daily_averages),
        topic_datasets=json.dumps({}),
        all_topics=json.dumps([])
    )


@main_bp.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not current_user.check_password(current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/delete-account', methods=['POST'])
@login_required
def delete_account():
    try:
        data = request.get_json()
        password = data.get('password')
        
        if not current_user.check_password(password):
            return jsonify({'success': False, 'message': 'Password is incorrect'}), 400
        
        QuizResult.query.filter_by(user_id=current_user.id).delete()
        db.session.delete(current_user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/upload-profile-picture', methods=['POST'])
@login_required
def upload_profile_picture():
    try:
        if 'profile_picture' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'}), 400
        
        file = request.files['profile_picture']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"user_{current_user.id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
            os.makedirs(upload_path, exist_ok=True)
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
            
            if current_user.profile_picture:
                old_file_path = os.path.join(upload_path, current_user.profile_picture)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            current_user.profile_picture = filename
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Profile picture uploaded successfully'})
        else:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@main_bp.route('/api/remove-profile-picture', methods=['POST'])
@login_required
def remove_profile_picture():
    try:
        if current_user.profile_picture:
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', 'profile_pictures')
            file_path = os.path.join(upload_path, current_user.profile_picture)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            current_user.profile_picture = None
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile picture removed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


# ========== NOTIFICATION ROUTES (SIMPLE VERSION) ==========

@main_bp.route('/api/notifications')
@login_required
def get_notifications():
    """Get user's notifications for badge count"""
    limit = request.args.get('limit', 50, type=int)
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    notifications_data = []
    for notification in notifications:
        notifications_data.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'is_read': notification.is_read,
            'icon': notification.icon,
            'created_at': notification.created_at.isoformat(),
            'time_ago': notification.get_time_ago(),
            'action_url': notification.action_url
        })
    
    return jsonify({
        'success': True, 
        'notifications': notifications_data,
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    })


@main_bp.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read_simple(notification_id):
    """Mark a single notification as read"""
    try:
        notification = Notification.query.get_or_404(notification_id)
        if notification.user_id == current_user.id:
            notification.is_read = True
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read_simple():
    """Mark all notifications as read"""
    try:
        Notification.query.filter_by(
            user_id=current_user.id,
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
        return jsonify({'success': True, 'message': 'All notifications marked as read'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/notifications')
@login_required
def notifications_page():
    """Simple notifications page"""
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications_simple.html',
                         notifications=notifications,
                         title='Notifications')


# ========== NOTES API ROUTES ==========

@main_bp.route('/api/notes', methods=['GET'])
@login_required
def get_notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
    return jsonify({'success': True, 'notes': [note.to_dict() for note in notes]})


@main_bp.route('/api/notes', methods=['POST'])
@login_required
def create_note():
    try:
        data = request.get_json()
        
        note = Note(
            user_id=current_user.id,
            title=data.get('title', 'Untitled'),
            content=data.get('content', ''),
            color=data.get('color', 'bg-yellow-100'),
            border_color=data.get('borderColor', 'border-yellow-300')
        )
        
        db.session.add(note)
        db.session.commit()
        
        return jsonify({'success': True, 'note': note.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/notes/<int:note_id>', methods=['PUT'])
@login_required
def update_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        
        if note.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            note.title = data['title']
        if 'content' in data:
            note.content = data['content']
        if 'color' in data:
            note.color = data['color']
        if 'borderColor' in data:
            note.border_color = data['borderColor']
        
        note.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'note': note.to_dict()})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required
def delete_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        
        if note.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        db.session.delete(note)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Note deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== ADDITIONAL PAGES ==========

@main_bp.route('/abe-applications')
@login_required
def abe_applications():
    applications = [
        {
            'name': 'PAES App',
            'description': 'Download our version of PAES App for Android.',
            'url': 'https://drive.google.com/your-paes-app-link',
            'icon': 'fas fa-mobile-alt'
        },
        {
            'name': 'Open Channels Calculator',
            'description': 'Tools for open channel flow calculations and design.',
            'url': 'https://drive.google.com/your-open-channels-calculator-link',
            'icon': 'fas fa-calculator'
        },
        {
            'name': 'Farm Machinery Calculator',
            'description': 'Tools for farm machinery selection and calculations.',
            'url': 'https://drive.google.com/your-farm-machinery-calculator-link',
            'icon': 'fas fa-tractor'
        },
    ]
    return render_template('abe_applications.html', 
                         applications=applications,
                         title='ABE Applications')


@main_bp.route('/announcements')
@login_required
def announcement_board():
    announcements = Announcement.query.filter_by(is_active=True).order_by(
        Announcement.is_pinned.desc(),
        Announcement.created_at.desc()
    ).all()
    
    return render_template('announcements/index.html',
                         announcements=announcements,
                         title='Announcement Board')


@main_bp.route('/about-us')
@login_required
def about_us():
    return render_template('about_us.html', title='About Us')


@main_bp.route('/contact-support')
@login_required
def contact_support():
    return render_template('contact_support.html', title='Contact Support')


@main_bp.route('/privacy-policy')
@login_required
def privacy_policy():
    from datetime import datetime
    return render_template('privacy_policy.html', 
                         title='Privacy Policy',
                         now=datetime.now())

@main_bp.route('/api/user-streak')
@login_required
def get_user_streak():
    from datetime import date, timedelta
    from sqlalchemy import func
    
    all_results_dates = db.session.query(
        func.date(QuizResult.completed_at).label('quiz_date')
    ).filter(
        QuizResult.user_id == current_user.id,
        QuizResult.completed_at.isnot(None)
    ).group_by(
        func.date(QuizResult.completed_at)
    ).order_by(
        desc('quiz_date')
    ).all()
    
    quiz_dates = set(r.quiz_date for r in all_results_dates if r.quiz_date is not None)
    
    streak = 0
    today_local = date.today()
    current_date = today_local if today_local in quiz_dates else (today_local - timedelta(days=1))
    
    while current_date in quiz_dates:
        streak += 1
        current_date -= timedelta(days=1)
    
    return jsonify({'success': True, 'streak': streak})


# ========== STUDY REMINDER ROUTES ==========

@main_bp.route('/api/reminders', methods=['GET'])
@login_required
def get_reminders():
    """Get all reminders for the current user"""
    try:
        from app.models import StudyReminder
        reminders = StudyReminder.query.filter_by(user_id=current_user.id).all()
        return jsonify({
            'success': True,
            'reminders': [r.to_dict() for r in reminders]
        })
    except Exception as e:
        print(f"Error in get_reminders: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/reminders', methods=['POST'])
@login_required
def create_reminder():
    """Create a new reminder"""
    try:
        from app.models import StudyReminder
        data = request.get_json()
        
        reminder = StudyReminder(
            user_id=current_user.id,
            date=data.get('date'),
            time=data.get('time'),
            title=data.get('title', 'Study Session'),
            topic=data.get('topic', 'General'),
            completed=False,
            snoozed=False
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reminder': reminder.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in create_reminder: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/reminders/<int:reminder_id>', methods=['PUT'])
@login_required
def update_reminder(reminder_id):
    """Update a reminder"""
    try:
        from app.models import StudyReminder
        reminder = StudyReminder.query.get_or_404(reminder_id)
        
        if reminder.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'completed' in data:
            reminder.completed = data['completed']
        if 'snoozed' in data:
            reminder.snoozed = data['snoozed']
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error in update_reminder: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/reminders/<int:reminder_id>', methods=['DELETE'])
@login_required
def delete_reminder(reminder_id):
    """Delete a reminder"""
    try:
        from app.models import StudyReminder
        reminder = StudyReminder.query.get_or_404(reminder_id)
        
        if reminder.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        db.session.delete(reminder)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error in delete_reminder: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== DEBUG ROUTES ==========

@main_bp.route('/debug-messages')
def debug_messages():
    return render_template('debug_messages.html')


@main_bp.route('/list-routes')
def list_routes():
    routes = []
    for rule in current_app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        routes.append({
            'endpoint': rule.endpoint,
            'methods': methods,
            'rule': rule.rule
        })
    
    routes.sort(key=lambda x: x['rule'])
    
    html = "<h1>All Routes</h1><ul>"
    for route in routes:
        html += f"<li><strong>{route['rule']}</strong> → {route['endpoint']} ({route['methods']})</li>"
    html += "</ul>"
    
    return html