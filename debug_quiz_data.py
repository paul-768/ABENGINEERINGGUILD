import sqlite3
import os

DB_PATH = 'data/quizzes.db'

def debug_quiz_data():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATABASE DEBUG INFO")
    print("="*60)
    
    # Check quiz_results table structure
    cursor.execute("PRAGMA table_info(quiz_result)")
    columns = cursor.fetchall()
    print("\n📋 quiz_result table columns:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Get all quiz results
    cursor.execute("SELECT id, user_id, topic_id, score, total_questions, percentage, time_taken, completed_at FROM quiz_result ORDER BY completed_at DESC")
    results = cursor.fetchall()
    
    print(f"\n📊 QUIZ RESULTS ({len(results)} total):")
    if results:
        for r in results:
            print(f"   ID: {r[0]}, User: {r[1]}, Topic: {r[2]}, Score: {r[3]}%, Total: {r[4]}, Percentage: {r[5]}%, Date: {r[7]}")
    else:
        print("   ❌ NO QUIZ RESULTS FOUND!")
    
    # Check users
    cursor.execute("SELECT id, name, email FROM user")
    users = cursor.fetchall()
    print(f"\n👤 USERS ({len(users)}):")
    for u in users:
        print(f"   ID: {u[0]}, Name: {u[1]}, Email: {u[2]}")
    
    # Check questions
    cursor.execute("SELECT COUNT(*) FROM question")
    question_count = cursor.fetchone()[0]
    print(f"\n❓ QUESTIONS in database: {question_count}")
    
    if question_count == 0:
        print("   ⚠️ No questions found! Run seed_questions.py first.")
    
    conn.close()

if __name__ == '__main__':
    debug_quiz_data()