# reset_achievements.py
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Resetting achievements...")
    
    # Clear user achievements
    db.session.execute(text('DELETE FROM user_achievement'))
    print("✓ Cleared user_achievement table")
    
    # Clear achievements
    db.session.execute(text('DELETE FROM achievement'))
    print("✓ Cleared achievement table")
    
    db.session.commit()
    print("Done! Now run: python seed_achievements.py")