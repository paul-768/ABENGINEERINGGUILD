import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = 'data/quizzes.db'

def check_quiz_dates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("CHECKING QUIZ RESULT DATES")
    print("="*60)
    
    # Get all quiz results
    cursor.execute("""
        SELECT id, user_id, score, completed_at, DATE(completed_at)
        FROM quiz_result
        ORDER BY completed_at DESC
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("❌ NO QUIZ RESULTS FOUND IN DATABASE!")
        print("\nYou need to take a quiz first.")
        conn.close()
        return
    
    print(f"\n📊 Found {len(results)} quiz results:\n")
    
    for r in results:
        print(f"  ID: {r[0]}, User: {r[1]}, Score: {r[2]}%, Date: {r[4]}, Full: {r[3]}")
    
    # Check last 7 days
    seven_days_ago = (datetime.now() - timedelta(days=7)).date()
    print(f"\n📅 Checking quizzes in last 7 days (since {seven_days_ago}):")
    
    recent = [r for r in results if datetime.strptime(r[4], '%Y-%m-%d').date() >= seven_days_ago]
    
    if recent:
        print(f"  ✅ Found {len(recent)} quizzes in last 7 days!")
        for r in recent:
            print(f"     - Score: {r[2]}% on {r[4]}")
    else:
        print(f"  ❌ No quizzes in last 7 days!")
        print(f"     Your last quiz was on {results[0][4] if results else 'never'}")
        print(f"     That's {(datetime.now().date() - datetime.strptime(results[0][4], '%Y-%m-%d').date()).days} days ago")
    
    conn.close()

if __name__ == '__main__':
    check_quiz_dates()