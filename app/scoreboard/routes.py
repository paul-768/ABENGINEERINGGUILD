# app/scoreboard/routes.py - COMPLETE FIXED VERSION WITH RANK CHANGE NOTIFICATIONS
from flask import render_template, request, jsonify, flash, redirect, session, url_for
from flask_login import login_required, current_user
from app.models import User, QuizResult, Topic, Notification
from app.scoreboard.analytics import get_scoreboard_data, get_top_scorers_data, get_user_progress, get_topic_mastery, get_performance_grid_data
from app.scoreboard import scoreboard_bp
from datetime import datetime, timedelta
from sqlalchemy import func, case
from app import db


def check_and_notify_rank_change(user_id):
    """Check if user's rank changed and send notification"""
    # Get current rank
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=30)  # Use 30-day rank
    
    raw_data = get_scoreboard_data(start_date)
    
    new_rank = None
    for idx, student in enumerate(raw_data, 1):
        if student['user_id'] == user_id:
            new_rank = idx
            new_score = student.get('custom_score', student.get('avg_score', 0))
            break
    
    if new_rank is None:
        return
    
    # Get previous rank from database or session
    # Store previous rank in a simple cache or database table
    # For simplicity, we'll check if user has a notification preference stored
    from app.models import UserPreference  # You may need to create this model
    
    # Get last known rank from a simple key-value store or session
    # Alternative: Compare with user's history
    previous_results = QuizResult.query.filter_by(user_id=user_id).count()
    
    # If this is first quiz, no need to notify
    if previous_results <= 1:
        return
    
    # Get previous rank from a simple calculation
    # For demo, we'll check if user moved into top 10
    if new_rank <= 10:
        # Check if user wasn't in top 10 before
        previous_data = get_scoreboard_data(start_date - timedelta(days=1))
        was_in_top_10 = False
        for student in previous_data:
            if student['user_id'] == user_id and student.get('rank', 999) <= 10:
                was_in_top_10 = True
                break
        
        if not was_in_top_10:
            notification = Notification(
                user_id=user_id,
                title="🏆 You're in the Top 10!",
                message=f"Congratulations! You are now ranked #{new_rank} on the scoreboard!",
                notification_type='rank_milestone',
                icon="fas fa-chart-line",
                action_url=url_for('scoreboard.scoreboard'),
                created_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            print(f"DEBUG - Rank milestone notification sent to user {user_id}")
    
    # Check if user reached #1
    if new_rank == 1:
        notification = Notification(
            user_id=user_id,
            title="👑 You're Number 1!",
            message="Congratulations! You are the top performer on the scoreboard!",
            notification_type='rank_number_one',
            icon="fas fa-crown",
            action_url=url_for('scoreboard.scoreboard'),
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
        print(f"DEBUG - Number one notification sent to user {user_id}")


@scoreboard_bp.route('/scoreboard')
@login_required
def scoreboard():
    filter_type = request.args.get('filter', 'all-time')
    
    today = datetime.utcnow().date()
    if filter_type == 'today':
        start_date = today
    elif filter_type == 'week':
        start_date = today - timedelta(days=7)
    elif filter_type == 'month':
        start_date = today - timedelta(days=30)
    else:
        start_date = None
    
    raw_data = get_scoreboard_data(start_date)
    top_scorers = get_top_scorers_data(start_date)
    
    # Add rank numbers based on custom formula sorting
    for idx, student in enumerate(raw_data, 1):
        student['rank'] = idx
    
    # Get current user's rank info
    user_rank_info = None
    for student in raw_data:
        if student['user_id'] == current_user.id:
            user_rank_info = student
            break
    
    # Check rank change for current user
    if user_rank_info:
        check_and_notify_rank_change(current_user.id)
    
    return render_template('scoreboard.html',
                         title='Scoreboard',
                         scoreboard_data=raw_data,
                         top_scorers=top_scorers,
                         user_rank_info=user_rank_info,
                         filter_type=filter_type)


@scoreboard_bp.route('/analytics')
@login_required
def analytics():
    # Get basic progress data (7 days)
    progress_data = get_user_progress(current_user.id, days=7)
    topic_performance = get_topic_mastery(current_user.id)
    performance_grid = get_performance_grid_data(current_user.id)
    
    # Calculate user statistics
    user_stats = db.session.query(
        func.count(QuizResult.id).label('total_quizzes'),
        func.sum(QuizResult.total_questions).label('total_questions'),
        func.sum(
            case(
                (QuizResult.total_questions > 0, 
                 (QuizResult.score / 100.0) * QuizResult.total_questions),
                else_=0
            )
        ).label('total_correct'),
        func.avg(QuizResult.score).label('avg_score')
    ).filter(QuizResult.user_id == current_user.id).first()
    
    total_correct = float(user_stats.total_correct or 0)
    total_questions = user_stats.total_questions or 0
    accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    average_score = round(user_stats.avg_score or 0, 2)
    
    # Calculate custom rank score for current user
    rank_score = (average_score + accuracy) / 2
    
    # Identify weak and strong areas
    weak_areas = [t for t in topic_performance if t['score'] < 70]
    strong_areas = [t for t in topic_performance if t['score'] >= 70]
    
    weak_areas.sort(key=lambda x: x['score'])
    strong_areas.sort(key=lambda x: x['score'], reverse=True)
    
    # Generate subject progress data for the multi-subject chart
    subject_progress_data = get_subject_progress_data(current_user.id, days=7)
    
    # ========== CHECK FOR WEAK AREA NOTIFICATIONS ==========
    # Send notification if user has consistent low scores in a topic
    for weak_topic in weak_areas:
      if weak_topic['score'] < 50 and weak_topic.get('attempts', 0) >= 2:
            # Check if we already notified about this topic recently
            recent_notification = Notification.query.filter(
                Notification.user_id == current_user.id,
                Notification.notification_type == 'weak_area_alert',
                Notification.created_at >= datetime.utcnow() - timedelta(days=3)
            ).first()
            
            if not recent_notification:
                notification = Notification(
                    user_id=current_user.id,
                    title="📚 Need Improvement",
                    message=f"Your score in {weak_topic['topic_name']} is {weak_topic['score']:.1f}%. Focus more on this topic!",
                    notification_type='weak_area_alert',
                    icon="fas fa-exclamation-triangle",
                    action_url=url_for('scoreboard.analytics'),
                    created_at=datetime.utcnow()
                )
                db.session.add(notification)
                db.session.commit()
    # ========== END NOTIFICATION ==========
    
    # ========== CHECK FOR IMPROVEMENT NOTIFICATION ==========
    # Check if user improved significantly
    if len(progress_data) >= 4:
        recent_avg = sum(progress_data[-2:]) / 2 if len(progress_data[-2:]) > 0 else 0
        previous_avg = sum(progress_data[-4:-2]) / 2 if len(progress_data[-4:-2]) > 0 else 0
        
        if recent_avg > previous_avg + 15 and recent_avg > 0:
            # Check if we already notified about improvement recently
            recent_improvement = Notification.query.filter(
                Notification.user_id == current_user.id,
                Notification.notification_type == 'improvement_alert',
                Notification.created_at >= datetime.utcnow() - timedelta(days=7)
            ).first()
            
            if not recent_improvement:
                notification = Notification(
                    user_id=current_user.id,
                    title="📈 Great Improvement!",
                    message=f"Your average score increased by {recent_avg - previous_avg:.1f}%! Keep up the momentum!",
                    notification_type='improvement_alert',
                    icon="fas fa-arrow-up",
                    action_url=url_for('scoreboard.analytics'),
                    created_at=datetime.utcnow()
                )
                db.session.add(notification)
                db.session.commit()
    # ========== END NOTIFICATION ==========
    
    return render_template('analytics.html',
                         title='Performance Analytics',
                         progress_data=progress_data,
                         topic_performance=topic_performance,
                         weak_areas=weak_areas,
                         strong_areas=strong_areas[:3],
                         performance_grid=performance_grid,
                         total_quizzes=user_stats.total_quizzes or 0,
                         total_correct=total_correct,
                         total_questions=total_questions,
                         accuracy=round(accuracy, 2),
                         average_score=average_score,
                         rank_score=round(rank_score, 2),
                         subject_progress_data=subject_progress_data)


def get_subject_progress_data(user_id, days=7):
    """
    Generate subject-specific progress data for the multi-subject chart.
    FIXED: Direct topic ID mapping for AREA I, II, III, Engineering Math, PAES.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Create date range for ALL days
    date_range = []
    current_date = start_date.date()
    while current_date <= end_date.date():
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    dates_formatted = [date.strftime('%m/%d') for date in date_range]
    
    # Initialize result with zeros
    result_data = {
        'dates': dates_formatted,
        'area_i': [0] * len(date_range),
        'area_ii': [0] * len(date_range),
        'area_iii': [0] * len(date_range),
        'engineering_math': [0] * len(date_range),
        'paes': [0] * len(date_range)
    }
    
    # Get ALL quiz results for the user within date range
    quiz_results = QuizResult.query.filter(
        QuizResult.user_id == user_id,
        QuizResult.completed_at.isnot(None),
        QuizResult.completed_at >= start_date
    ).all()
    
    print(f"\n{'='*60}")
    print(f"[DEBUG] User ID {user_id} - Found {len(quiz_results)} quiz results in last {days} days")
    print(f"{'='*60}")
    
    if not quiz_results:
        return result_data
    
    # Create a dictionary to store scores by date and category
    daily_scores = {}
    for date in date_range:
        daily_scores[date] = {
            'area_i': [],
            'area_ii': [],
            'area_iii': [],
            'engineering_math': [],
            'paes': []
        }
    
    # Process each quiz result using DIRECT TOPIC ID MAPPING
    for result in quiz_results:
        result_date = result.completed_at.date()
        
        if result_date not in daily_scores:
            continue
        
        topic_id = result.topic_id
        
        # DIRECT MAPPING based on your topic IDs
        if topic_id == 1:
            category = 'area_i'
            print(f"  -> Topic ID {topic_id} (AREA I) → Score: {result.score} on {result_date}")
        elif topic_id == 2:
            category = 'area_ii'
            print(f"  -> Topic ID {topic_id} (AREA II) → Score: {result.score} on {result_date}")
        elif topic_id == 3:
            category = 'area_iii'
            print(f"  -> Topic ID {topic_id} (AREA III) → Score: {result.score} on {result_date}")
        elif topic_id == 4:
            category = 'engineering_math'
            print(f"  -> Topic ID {topic_id} (Engineering Mathematics) → Score: {result.score} on {result_date}")
        elif topic_id == 5:
            category = 'paes'
            print(f"  -> Topic ID {topic_id} (PAES Standards) → Score: {result.score} on {result_date}")
        else:
            # Unknown topic - skip or default
            print(f"  -> WARNING: Unknown topic ID {topic_id} - skipping")
            continue
        
        # Add score to the appropriate category
        daily_scores[result_date][category].append(result.score)
    
    # Calculate daily averages
    for date_idx, date in enumerate(date_range):
        for category in ['area_i', 'area_ii', 'area_iii', 'engineering_math', 'paes']:
            scores = daily_scores[date][category]
            if scores:
                avg_score = round(sum(scores) / len(scores), 2)
                result_data[category][date_idx] = avg_score
    
    print(f"\n[DEBUG] Final Result for User {user_id}:")
    print(f"  AREA I: {result_data['area_i']}")
    print(f"  AREA II: {result_data['area_ii']}")
    print(f"  AREA III: {result_data['area_iii']}")
    print(f"  Engineering Math: {result_data['engineering_math']}")
    print(f"  PAES: {result_data['paes']}")
    print(f"{'='*60}\n")
    
    return result_data


@scoreboard_bp.route('/scoreboard/json')
@login_required
def scoreboard_json():
    filter_type = request.args.get('filter', 'all-time')
    
    today = datetime.utcnow().date()
    if filter_type == 'today':
        start_date = today
    elif filter_type == 'week':
        start_date = today - timedelta(days=7)
    elif filter_type == 'month':
        start_date = today - timedelta(days=30)
    else:
        start_date = None
    
    raw_data = get_scoreboard_data(start_date)
    top_scorers = get_top_scorers_data(start_date)
    
    for idx, student in enumerate(raw_data, 1):
        student['rank'] = idx
    
    user_rank_info = None
    for student in raw_data:
        if student['user_id'] == current_user.id:
            user_rank_info = student
            break
    
    return jsonify({
        'scoreboard': raw_data,
        'top_scorers': top_scorers,
        'user_rank_info': user_rank_info,
        'filter_type': filter_type
    })


@scoreboard_bp.route('/analytics/subject-data')
@login_required
def subject_progress_api():
    """API endpoint to get subject progress data for AJAX updates"""
    days = request.args.get('days', 7, type=int)
    data = get_subject_progress_data(current_user.id, days)
    return jsonify(data)