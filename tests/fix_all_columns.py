# fix_all_columns.py
import sqlite3
import os

def fix_all_tables():
    print("🔧 Fixing ALL database tables...")
    
    db_path = "data/quizzes.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Fix USER table
        cursor.execute("PRAGMA table_info(user)")
        user_columns = [column[1] for column in cursor.fetchall()]
        print("📋 User table columns:", user_columns)
        
        if 'notification_preferences' not in user_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN notification_preferences TEXT DEFAULT '{}'")
            print("✅ Added user.notification_preferences")
        
        if 'email_notifications' not in user_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN email_notifications BOOLEAN DEFAULT 1")
            print("✅ Added user.email_notifications")
            
        if 'push_notifications' not in user_columns:
            cursor.execute("ALTER TABLE user ADD COLUMN push_notifications BOOLEAN DEFAULT 1")
            print("✅ Added user.push_notifications")
        
        # Fix QUIZ_RESULT table
        cursor.execute("PRAGMA table_info(quiz_result)")
        quiz_result_columns = [column[1] for column in cursor.fetchall()]
        print("📋 Quiz_result table columns:", quiz_result_columns)
        
        if 'percentage' not in quiz_result_columns:
            cursor.execute("ALTER TABLE quiz_result ADD COLUMN percentage FLOAT")
            print("✅ Added quiz_result.percentage")
            
        if 'time_taken' not in quiz_result_columns:
            cursor.execute("ALTER TABLE quiz_result ADD COLUMN time_taken INTEGER")
            print("✅ Added quiz_result.time_taken")
        
        # Fix NOTIFICATION table
        cursor.execute("PRAGMA table_info(notification)")
        notification_columns = [column[1] for column in cursor.fetchall()]
        print("📋 Notification table columns:", notification_columns)
        
        if 'related_type' not in notification_columns:
            cursor.execute("ALTER TABLE notification ADD COLUMN related_type VARCHAR(50)")
            print("✅ Added notification.related_type")
            
        if 'action_url' not in notification_columns:
            cursor.execute("ALTER TABLE notification ADD COLUMN action_url VARCHAR(500)")
            print("✅ Added notification.action_url")
            
        if 'icon' not in notification_columns:
            cursor.execute("ALTER TABLE notification ADD COLUMN icon VARCHAR(100) DEFAULT 'fas fa-bell'")
            print("✅ Added notification.icon")
            
        if 'priority' not in notification_columns:
            cursor.execute("ALTER TABLE notification ADD COLUMN priority VARCHAR(20) DEFAULT 'normal'")
            print("✅ Added notification.priority")
            
        if 'expires_at' not in notification_columns:
            cursor.execute("ALTER TABLE notification ADD COLUMN expires_at DATETIME")
            print("✅ Added notification.expires_at")
        
        # Fix other tables
        cursor.execute("PRAGMA table_info(paes_standard)")
        paes_columns = [column[1] for column in cursor.fetchall()]
        if 'category' not in paes_columns:
            cursor.execute("ALTER TABLE paes_standard ADD COLUMN category VARCHAR(100)")
            print("✅ Added paes_standard.category")
        
        cursor.execute("PRAGMA table_info(saved_post)")
        saved_post_columns = [column[1] for column in cursor.fetchall()]
        if 'folder' not in saved_post_columns:
            cursor.execute("ALTER TABLE saved_post ADD COLUMN folder VARCHAR(100) DEFAULT 'general'")
            print("✅ Added saved_post.folder")
        
        cursor.execute("PRAGMA table_info(topic)")
        topic_columns = [column[1] for column in cursor.fetchall()]
        if 'color' not in topic_columns:
            cursor.execute("ALTER TABLE topic ADD COLUMN color VARCHAR(7) DEFAULT '#4CAF50'")
            print("✅ Added topic.color")
        
        conn.commit()
        conn.close()
        
        print("🎉 ALL database tables fixed successfully!")
        print("🚀 You can now run: python run.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()

if __name__ == "__main__":
    fix_all_tables()