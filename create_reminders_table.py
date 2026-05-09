# create_reminders_table.py
import sqlite3
import os

# Path to your database
db_path = os.path.join('data', 'quizzes.db')

def create_reminders_table():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create the study_reminders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date VARCHAR(20) NOT NULL,
                time VARCHAR(10) NOT NULL,
                title VARCHAR(200) NOT NULL,
                topic VARCHAR(100),
                completed BOOLEAN DEFAULT 0,
                snoozed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ study_reminders table created successfully!")
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_reminders'")
        if cursor.fetchone():
            print("✅ Table verified!")
        else:
            print("❌ Table not found!")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    create_reminders_table()