# app/achievements/routes.py - COMPLETE WITH ALL REQUIREMENT TYPES
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Achievement, UserAchievement, QuizResult, Topic, User, Post, Comment
from app.achievements import achievements_bp
from datetime import datetime, timedelta
from sqlalchemy import func, case

@achievements_bp.route('/')
@login_required
def index():
    """Display all achievements"""
    return render_template('achievements/index.html', title='Achievements')


@achievements_bp.route('/api/data')
@login_required
def get_achievements_data():
    """Get all achievements with user progress"""
    all_achievements = Achievement.query.order_by(Achievement.display_order, Achievement.id).all()
    
    # Get user's unlocked achievements
    unlocked_ids = [ua.achievement_id for ua in UserAchievement.query.filter_by(user_id=current_user.id).all()]
    
    # Calculate progress for each achievement
    achievements_data = []
    for achievement in all_achievements:
        is_unlocked = achievement.id in unlocked_ids
        
        # Calculate progress based on requirement type
        progress = calculate_achievement_progress(current_user.id, achievement)
        
        # Get unlocked_at date if unlocked
        unlocked_at = None
        if is_unlocked:
            ua = UserAchievement.query.filter_by(
                user_id=current_user.id, 
                achievement_id=achievement.id
            ).first()
            if ua:
                unlocked_at = ua.unlocked_at
        
        achievements_data.append({
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'points': achievement.points,
            'category': achievement.category,
            'badge_color': achievement.badge_color,
            'is_unlocked': is_unlocked,
            'progress': round(progress, 1),
            'unlocked_at': unlocked_at.isoformat() if unlocked_at else None,
            'requirement_type': achievement.requirement_type,
            'requirement_value': achievement.requirement_value
        })
    
    # Get user stats for summary
    total_unlocked = len(unlocked_ids)
    total_points = sum(a.points for a in all_achievements if a.id in unlocked_ids)
    total_achievements = len(all_achievements)
    
    # Get recent achievements (last 5 unlocked)
    recent = UserAchievement.query.filter_by(user_id=current_user.id)\
        .order_by(UserAchievement.unlocked_at.desc()).limit(5).all()
    
    recent_data = []
    for ra in recent:
        achievement = Achievement.query.get(ra.achievement_id)
        if achievement:
            recent_data.append({
                'id': achievement.id,
                'name': achievement.name,
                'icon': achievement.icon,
                'points': achievement.points,
                'unlocked_at': ra.unlocked_at.isoformat()
            })
    
    return jsonify({
        'success': True,
        'achievements': achievements_data,
        'stats': {
            'total_unlocked': total_unlocked,
            'total_points': total_points,
            'total_achievements': total_achievements,
            'completion_percentage': round((total_unlocked / total_achievements) * 100, 1) if total_achievements > 0 else 0
        },
        'recent': recent_data
    })


def calculate_achievement_progress(user_id, achievement):
    """Calculate user's progress toward an achievement"""
    
    # QUIZ COUNT
    if achievement.requirement_type == 'quiz_count':
        count = QuizResult.query.filter_by(user_id=user_id).count()
        return min(100, (count / achievement.requirement_value) * 100)
    
    # PERFECT SCORE
    elif achievement.requirement_type == 'perfect_score':
        count = QuizResult.query.filter_by(user_id=user_id, score=100).count()
        return min(100, (count / achievement.requirement_value) * 100)
    
    # HIGH AVERAGE SCORE
    elif achievement.requirement_type == 'high_score':
        avg_score = db.session.query(func.avg(QuizResult.score)).filter_by(user_id=user_id).scalar() or 0
        return min(100, (avg_score / achievement.requirement_value) * 100)
    
    # STREAK
    elif achievement.requirement_type == 'streak':
        streak = calculate_user_streak(user_id)
        return min(100, (streak / achievement.requirement_value) * 100)
    
    # TOPIC MASTERY (score threshold for specific topic)
    elif achievement.requirement_type == 'topic_mastery':
        topic_id = int(achievement.requirement_extra) if achievement.requirement_extra else None
        if topic_id:
            avg_score = db.session.query(func.avg(QuizResult.score)).filter_by(
                user_id=user_id, topic_id=topic_id
            ).scalar() or 0
            return min(100, (avg_score / achievement.requirement_value) * 100)
        return 0
    
    # TOPIC QUIZ COUNT (number of quizzes in specific topic)
    elif achievement.requirement_type == 'topic_quiz_count':
        topic_id = int(achievement.requirement_extra) if achievement.requirement_extra else None
        if topic_id:
            count = QuizResult.query.filter_by(user_id=user_id, topic_id=topic_id).count()
            return min(100, (count / achievement.requirement_value) * 100)
        return 0
    
    # TOPIC PERFECT SCORE (perfect score in specific topic)
    elif achievement.requirement_type == 'topic_perfect_score':
        topic_id = int(achievement.requirement_extra) if achievement.requirement_extra else None
        if topic_id:
            count = QuizResult.query.filter_by(user_id=user_id, topic_id=topic_id, score=100).count()
            return min(100, (count / achievement.requirement_value) * 100) if achievement.requirement_value > 0 else (100 if count > 0 else 0)
        return 0
    
    # TOPIC COMPLETION (answered all questions in topic)
    elif achievement.requirement_type == 'topic_completion':
        # This requires tracking unique questions answered per topic
        # For now, return 0 - implement based on your question bank
        return 0
    
    # TOPIC HIGH AVERAGE (high average on 20+ quizzes)
    elif achievement.requirement_type == 'topic_high_avg':
        topic_id = int(achievement.requirement_extra) if achievement.requirement_extra else None
        if topic_id:
            results = QuizResult.query.filter_by(user_id=user_id, topic_id=topic_id).all()
            if len(results) >= 20:
                avg_score = sum(r.score for r in results) / len(results)
                return min(100, (avg_score / achievement.requirement_value) * 100)
        return 0
    
    # ALL TOPICS MASTERY
    elif achievement.requirement_type == 'all_topics_mastery':
        topics = Topic.query.all()
        if not topics:
            return 0
        mastered = 0
        for topic in topics:
            avg_score = db.session.query(func.avg(QuizResult.score)).filter_by(
                user_id=user_id, topic_id=topic.id
            ).scalar() or 0
            if avg_score >= achievement.requirement_value:
                mastered += 1
        return min(100, (mastered / len(topics)) * 100)
    
    # TOTAL QUESTIONS ANSWERED
    elif achievement.requirement_type == 'total_questions':
        total = db.session.query(func.sum(QuizResult.total_questions)).filter_by(user_id=user_id).scalar() or 0
        return min(100, (total / achievement.requirement_value) * 100)
    
    # RANK POSITION
    elif achievement.requirement_type == 'rank_position':
        # Get user's rank from scoreboard
        from app.scoreboard.analytics import get_user_rank
        rank = get_user_rank(user_id)
        if rank and rank <= achievement.requirement_value:
            return 100
        return 0
    
    # FRIENDS COUNT
    elif achievement.requirement_type == 'friends_count':
        from app.models import Friendship
        count = Friendship.query.filter(
            ((Friendship.user_id == user_id) | (Friendship.friend_id == user_id)) &
            (Friendship.status == 'accepted')
        ).count()
        return min(100, (count / achievement.requirement_value) * 100)
    
    # POSTS COUNT
    elif achievement.requirement_type == 'posts_count':
        count = Post.query.filter_by(user_id=user_id).count()
        return min(100, (count / achievement.requirement_value) * 100)
    
    # COMMENTS COUNT
    elif achievement.requirement_type == 'comments_count':
        count = Comment.query.filter_by(user_id=user_id).count()
        return min(100, (count / achievement.requirement_value) * 100)
    
    # STUDY DAYS
    elif achievement.requirement_type == 'study_days':
        dates = db.session.query(func.date(QuizResult.completed_at)).filter_by(user_id=user_id).distinct().count()
        return min(100, (dates / achievement.requirement_value) * 100)
    
    # TIME SPENT (minutes)
    elif achievement.requirement_type == 'time_spent':
        total_time = db.session.query(func.sum(QuizResult.time_taken)).filter_by(user_id=user_id).scalar() or 0
        minutes = total_time / 60 if total_time else 0
        return min(100, (minutes / achievement.requirement_value) * 100)
    
    # ACHIEVEMENT PERCENTAGE (Grand Master)
    elif achievement.requirement_type == 'achievement_percentage':
        total_achievements = Achievement.query.count()
        if total_achievements == 0:
            return 0
        unlocked_count = UserAchievement.query.filter_by(user_id=user_id).count()
        percentage = (unlocked_count / total_achievements) * 100
        return min(100, (percentage / achievement.requirement_value) * 100)
    
    else:
        return 0


def calculate_user_streak(user_id):
    """Calculate user's current study streak in days"""
    results = QuizResult.query.filter_by(user_id=user_id)\
        .order_by(QuizResult.completed_at.desc()).all()
    
    if not results:
        return 0
    
    streak = 0
    last_date = None
    
    for result in results:
        result_date = result.completed_at.date()
        
        if last_date is None:
            streak = 1
            last_date = result_date
        else:
            day_diff = (last_date - result_date).days
            if day_diff == 1:
                streak += 1
                last_date = result_date
            elif day_diff > 1:
                break
    
    return streak


@achievements_bp.route('/api/check')
@login_required
def check_achievements():
    """Check and unlock achievements for current user"""
    unlocked = []
    all_achievements = Achievement.query.all()
    
    for achievement in all_achievements:
        # Check if already unlocked
        existing = UserAchievement.query.filter_by(
            user_id=current_user.id,
            achievement_id=achievement.id
        ).first()
        
        if existing:
            continue
        
        # Check if requirements are met
        progress = calculate_achievement_progress(current_user.id, achievement)
        
        if progress >= 100:
            # Unlock achievement
            user_achievement = UserAchievement(
                user_id=current_user.id,
                achievement_id=achievement.id,
                progress=100,
                unlocked_at=datetime.utcnow()
            )
            db.session.add(user_achievement)
            unlocked.append({
                'id': achievement.id,
                'name': achievement.name,
                'icon': achievement.icon,
                'points': achievement.points
            })
    
    if unlocked:
        db.session.commit()
    
    return jsonify({
        'success': True,
        'unlocked': unlocked
    })


@achievements_bp.route('/api/stats')
@login_required
def get_achievement_stats():
    """Get user achievement statistics for dashboard"""
    total_achievements = Achievement.query.count()
    unlocked_count = UserAchievement.query.filter_by(user_id=current_user.id).count()
    total_points = db.session.query(func.sum(Achievement.points))\
        .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)\
        .filter(UserAchievement.user_id == current_user.id).scalar() or 0
    
    # Get recent unlocks (last 3)
    recent_unlocks = UserAchievement.query.filter_by(user_id=current_user.id)\
        .order_by(UserAchievement.unlocked_at.desc()).limit(3).all()
    
    recent_data = []
    for ru in recent_unlocks:
        achievement = Achievement.query.get(ru.achievement_id)
        if achievement:
            recent_data.append({
                'name': achievement.name,
                'icon': achievement.icon,
                'badge_color': achievement.badge_color,
                'unlocked_at': ru.unlocked_at.strftime('%b %d, %Y')
            })
    
    return jsonify({
        'success': True,
        'total_achievements': total_achievements,
        'unlocked_count': unlocked_count,
        'total_points': total_points,
        'completion_percentage': round((unlocked_count / total_achievements) * 100, 1) if total_achievements > 0 else 0,
        'recent_unlocks': recent_data
    })