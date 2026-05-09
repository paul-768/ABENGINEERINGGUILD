# fix_now.py
import sqlite3
import os

def fix_database():
    print("🔧 Fixing database...")
    
    # Try different possible database locations
    db_paths = [
        "data/quizzes.db",
        "instance/quizzes.db", 
        "quizzes.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"📁 Found database at: {db_path}")
            break
    else:
        print("❌ Could not find database file")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        print("📋 Current columns:", columns)
        
        # Add missing columns
        if 'notification_preferences' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN notification_preferences TEXT DEFAULT '{}'")
            print("✅ Added notification_preferences")
        
        if 'email_notifications' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN email_notifications BOOLEAN DEFAULT 1")
            print("✅ Added email_notifications")
            
        if 'push_notifications' not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN push_notifications BOOLEAN DEFAULT 1")
            print("✅ Added push_notifications")
        
        conn.commit()
        conn.close()
        
        print("🎉 Database fixed successfully!")
        print("🚀 You can now run: python run.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_database()