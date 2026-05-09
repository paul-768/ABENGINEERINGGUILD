# generate_activity.py
import sys
import os
sys.path.append('.')

from app import create_app, db
from app.models import User, Notification
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    user = User.query.first()
    if user:
        # Create realistic activity notifications
        activities = [
            {
                'title': '📚 Study Suggestion',
                'message': 'Based on your progress, we recommend reviewing Farm Machinery topics next',
                'type': 'study_suggestion',
                'icon': 'fas fa-lightbulb'
            },
            {
                'title': '🏆 Quiz Master',
                'message': 'You have completed 5 quizzes this week! Keep up the great work!',
                'type': 'achievement', 
                'icon': 'fas fa-trophy'
            },
            {
                'title': '📅 Study Reminder',
                'message': 'Your scheduled study session for Soil & Water Management starts in 1 hour',
                'type': 'study_reminder',
                'icon': 'fas fa-calendar-check'
            },
            {
                'title': '👥 Community Update',
                'message': '3 new discussions started in topics you follow',
                'type': 'community_update',
                'icon': 'fas fa-users'
            }
        ]
        
        for i, activity in enumerate(activities):
            # Create notifications from recent to older
            notification = Notification(
                user_id=user.id,
                title=activity['title'],
                message=activity['message'],
                notification_type=activity['type'],
                icon=activity['icon'],
                created_at=datetime.utcnow() - timedelta(hours=i*3)
            )
            db.session.add(notification)
        
        db.session.commit()
        print("✅ Real activity notifications created!")
        print("🔔 Refresh your page and click the bell to see real notifications!")