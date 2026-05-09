# clear_achievements_history.py
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Clear all user achievement records
    db.session.execute(text('DELETE FROM user_achievement'))
    db.session.commit()
    print("✓ Cleared all user achievement history")
    
    # Check counts
    from app.models import Achievement
    count = Achievement.query.count()
    print(f"✓ {count} achievements available in database")

print("\nDone! Restart your Flask app and refresh the page.")