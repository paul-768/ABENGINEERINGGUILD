# test_notification_mark.py
from app import create_app, db
from app.models import Notification

app = create_app()

with app.app_context():
    # Check unread count before
    unread_before = Notification.query.filter_by(user_id=1, is_read=False).count()
    print(f"Unread notifications BEFORE: {unread_before}")
    
    # Mark all as read
    result = Notification.query.filter_by(user_id=1, is_read=False).update({'is_read': True})
    db.session.commit()
    print(f"Marked {result} notifications as read")
    
    # Check after
    unread_after = Notification.query.filter_by(user_id=1, is_read=False).count()
    print(f"Unread notifications AFTER: {unread_after}")