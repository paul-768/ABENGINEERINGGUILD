# fix_migration.py
import sqlite3
import os
from app import create_app

def fix_database():
    app = create_app()
    
    with app.app_context():
        # Get the database path from app config
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Add new columns to user table
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'notification_preferences' not in columns:
                cursor.execute("ALTER TABLE user ADD COLUMN notification_preferences TEXT DEFAULT '{}'")
                print("✓ Added notification_preferences column")
            
            if 'email_notifications' not in columns:
                cursor.execute("ALTER TABLE user ADD COLUMN email_notifications BOOLEAN DEFAULT 1")
                print("✓ Added email_notifications column")
            
            if 'push_notifications' not in columns:
                cursor.execute("ALTER TABLE user ADD COLUMN push_notifications BOOLEAN DEFAULT 1")
                print("✓ Added push_notifications column")
            
            # Commit changes
            conn.commit()
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    fix_database()