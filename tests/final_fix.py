# final_fix.py
import sqlite3
import os
from app import create_app

def apply_fix():
    app = create_app()
    
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"📁 Database path: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check current columns
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            print("📋 Current user table columns:", columns)
            
            # Add missing columns
            missing_columns = []
            
            if 'notification_preferences' not in columns:
                cursor.execute("ALTER TABLE user ADD COLUMN notification_preferences TEXT DEFAULT '{}'")
                missing_columns.append('notification_preferences')
                
            if 'email_notifications' not in columns:
                cursor.execute("ALTER TABLE user ADD COLUMN email_notifications BOOLEAN DEFAULT 1")
                missing_columns.append('email_notifications')
                
            if 'push_notifications' not in columns:
                cursor.execute("ALTER TABLE user ADD COLUMN push_notifications BOOLEAN DEFAULT 1")
                missing_columns.append('push_notifications')
            
            conn.commit()
            
            if missing_columns:
                print(f"✅ Added columns: {missing_columns}")
            else:
                print("✅ All columns already exist")
                
            # Verify the fix
            cursor.execute("PRAGMA table_info(user)")
            new_columns = [column[1] for column in cursor.fetchall()]
            print("📋 Updated user table columns:", new_columns)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    apply_fix()