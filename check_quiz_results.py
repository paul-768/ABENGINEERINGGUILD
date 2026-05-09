import sqlite3
import os

DB_PATH = 'data/quizzes.db'

def check_quiz_results():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check quiz_results table
    cursor.execute("SELECT id, user_id, topic_id, score, total_questions, percentage, completed_at FROM quiz_result ORDER BY completed_at DESC")
    results = cursor.fetchall()
    
    print(f"\n=== QUIZ RESULTS ({len(results)} total) ===")
    for r in results:
        print(f"ID: {r[0]}, User: {r[1]}, Topic: {r[2]}, Score: {r[3]}%, Total Q: {r[4]}, Date: {r[6]}")
    
    # Check if results exist for current user
    cursor.execute("SELECT DISTINCT user_id FROM quiz_result")
    users = cursor.fetchall()
    print(f"\nUsers with quiz results: {[u[0] for u in users]}")
    
    conn.close()

if __name__ == '__main__':
    check_quiz_results()