# app/achievements/helpers.py
from app import db
from app.models import Achievement, UserAchievement, QuizResult, Topic
from flask_login import current_user
from datetime import datetime


def check_and_unlock_achievements(user_id, trigger_type=None, trigger_data=None):
    """
    Check and unlock achievements for a user.
    Call this after quiz completions, friend additions, etc.
    
    trigger_type: 'quiz_complete', 'perfect_score', 'friend_added', 'post_created', etc.
    """
    from app.achievements.routes import calculate_achievement_progress
    
    unlocked = []
    all_achievements = Achievement.query.all()
    
    for achievement in all_achievements:
        # Check if already unlocked
        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=achievement.id
        ).first()
        
        if existing:
            continue
        
        # Check if requirements are met
        progress = calculate_achievement_progress(user_id, achievement)
        
        if progress >= 100:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement.id,
                progress=100,
                unlocked_at=datetime.utcnow()
            )
            db.session.add(user_achievement)
            unlocked.append(achievement)
    
    if unlocked:
        db.session.commit()
    
    return unlocked


def get_user_achievement_summary(user_id):
    """Get summary of user's achievements for dashboard display"""
    unlocked = UserAchievement.query.filter_by(user_id=user_id).all()
    unlocked_ids = [ua.achievement_id for ua in unlocked]
    
    # Get all achievements with unlocked status
    all_achievements = Achievement.query.order_by(Achievement.display_order).all()
    
    unlocked_list = []
    locked_list = []
    
    for achievement in all_achievements:
        achievement_data = {
            'id': achievement.id,
            'name': achievement.name,
            'description': achievement.description,
            'icon': achievement.icon,
            'points': achievement.points,
            'badge_color': achievement.badge_color
        }
        
        if achievement.id in unlocked_ids:
            unlocked_list.append(achievement_data)
        else:
            locked_list.append(achievement_data)
    
    # Get recent achievements (last 5 unlocked)
    recent = UserAchievement.query.filter_by(user_id=user_id)\
        .order_by(UserAchievement.unlocked_at.desc()).limit(5).all()
    
    recent_data = []
    for r in recent:
        achievement = Achievement.query.get(r.achievement_id)
        if achievement:
            recent_data.append({
                'name': achievement.name,
                'icon': achievement.icon,
                'unlocked_at': r.unlocked_at.strftime('%b %d, %Y')
            })
    
    return {
        'total_unlocked': len(unlocked_ids),
        'total_points': sum(a.points for a in all_achievements if a.id in unlocked_ids),
        'recent': recent_data,
        'unlocked': unlocked_list,
        'locked': locked_list
    }