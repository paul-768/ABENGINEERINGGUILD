import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = 'data/quizzes.db'

def check_quiz_data():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("QUIZ DATA DEBUG")
    print("="*60)
    
    # Get users
    cursor.execute("SELECT id, name, email FROM user")
    users = cursor.fetchall()
    
    if not users:
        print("❌ No users found!")
        return
    
    print(f"\n👤 Users:")
    for u in users:
        print(f"   ID: {u[0]}, Name: {u[1]}")
        
        # Get quiz results for this user
        cursor.execute("""
            SELECT id, topic_id, score, percentage, DATE(completed_at), completed_at
            FROM quiz_result 
            WHERE user_id = ?
            ORDER BY completed_at DESC
        """, (u[0],))
        
        results = cursor.fetchall()
        
        print(f"\n   📊 Quiz Results for {u[1]} (User {u[0]}): {len(results)} total")
        
        if results:
            for r in results[:10]:  # Show last 10
                print(f"      - Score: {r[2]}%, Date: {r[4]}, Time: {r[5]}")
            
            # Check last 7 days
            seven_days_ago = (datetime.now() - timedelta(days=7)).date()
            recent = [r for r in results if datetime.strptime(r[4], '%Y-%m-%d').date() >= seven_days_ago]
            print(f"\n      📅 Last 7 days: {len(recent)} quizzes")
            
            if len(recent) == 0:
                print(f"      ⚠️ No quizzes in the last 7 days! Last quiz was on {results[0][4] if results else 'never'}")
        else:
            print("      ❌ No quiz results found!")
    
    conn.close()

if __name__ == '__main__':
    check_quiz_data()