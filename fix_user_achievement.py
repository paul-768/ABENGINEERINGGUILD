# fix_user_achievement.py
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Fixing user_achievement table...")
    
    # Add progress column to user_achievement table
    try:
        db.session.execute(text("ALTER TABLE user_achievement ADD COLUMN progress FLOAT DEFAULT 0"))
        print("✓ Added progress column to user_achievement")
    except Exception as e:
        if 'duplicate column name' in str(e).lower():
            print("✓ progress column already exists")
        else:
            print(f"Error: {e}")
    
    db.session.commit()
    print("Done!")