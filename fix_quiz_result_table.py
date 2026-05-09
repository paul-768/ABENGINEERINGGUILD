import sqlite3
import os

DB_PATH = 'data/quizzes.db'

def fix_quiz_result_table():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if percentage column exists
    cursor.execute("PRAGMA table_info(quiz_result)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'percentage' not in columns:
        print("Adding percentage column to quiz_result table...")
        cursor.execute("ALTER TABLE quiz_result ADD COLUMN percentage FLOAT")
        print("✅ percentage column added")
    
    if 'time_taken' not in columns:
        print("Adding time_taken column to quiz_result table...")
        cursor.execute("ALTER TABLE quiz_result ADD COLUMN time_taken INTEGER")
        print("✅ time_taken column added")
    
    # Update any existing rows where percentage is NULL
    cursor.execute("UPDATE quiz_result SET percentage = score WHERE percentage IS NULL")
    print(f"✅ Updated {cursor.rowcount} rows with percentage = score")
    
    conn.commit()
    conn.close()
    print("✅ Database fix completed!")

if __name__ == '__main__':
    fix_quiz_result_table()