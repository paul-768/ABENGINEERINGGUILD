import sqlite3
import os

def add_difficulty_column():
    # Path to your database
    db_path = os.path.join('data', 'quizzes.db')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if difficulty column already exists
        cursor.execute("PRAGMA table_info(question)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'difficulty' not in columns:
            print("Adding difficulty column to question table...")
            cursor.execute("ALTER TABLE question ADD COLUMN difficulty VARCHAR(20) DEFAULT 'medium'")
            conn.commit()
            print("Successfully added difficulty column")
        else:
            print("Difficulty column already exists")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    add_difficulty_column()