import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = 'data/quizzes.db'

def debug_chart_data():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("CHART DATA DEBUG")
    print("="*60)
    
    # Get current user (assuming user 1 for testing)
    cursor.execute("SELECT id, name FROM user LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found!")
        conn.close()
        return
    
    user_id = user[0]
    print(f"\n👤 Current User: {user[1]} (ID: {user_id})")
    
    # Get quiz results for last 7 days
    seven_days_ago = (datetime.now() - timedelta(days=6)).date()
    print(f"\n📅 Date range: {seven_days_ago} to {datetime.now().date()}")
    
    # Query daily averages
    cursor.execute("""
        SELECT 
            DATE(completed_at) as quiz_date,
            AVG(score) as avg_score,
            COUNT(*) as quiz_count
        FROM quiz_result 
        WHERE user_id = ? 
            AND completed_at IS NOT NULL
            AND DATE(completed_at) >= ?
        GROUP BY DATE(completed_at)
        ORDER BY quiz_date
    """, (user_id, seven_days_ago))
    
    results = cursor.fetchall()
    
    print(f"\n📊 Query Results ({len(results)} days with data):")
    if results:
        for r in results:
            print(f"   Date: {r[0]}, Avg Score: {r[1]}%, Quizzes: {r[2]}")
    else:
        print("   ❌ NO QUIZ RESULTS in last 7 days!")
    
    # Get ALL quiz results (not just last 7 days)
    cursor.execute("""
        SELECT COUNT(*), MIN(DATE(completed_at)), MAX(DATE(completed_at))
        FROM quiz_result 
        WHERE user_id = ?
    """, (user_id,))
    total_count, first_date, last_date = cursor.fetchone()
    
    print(f"\n📈 ALL TIME STATS:")
    print(f"   Total quizzes taken: {total_count}")
    print(f"   First quiz: {first_date}")
    print(f"   Last quiz: {last_date}")
    
    # Show all quiz results
    cursor.execute("""
        SELECT id, topic_id, score, percentage, DATE(completed_at)
        FROM quiz_result 
        WHERE user_id = ?
        ORDER BY completed_at DESC
        LIMIT 10
    """, (user_id,))
    
    print(f"\n📝 Last 10 Quiz Results:")
    for r in cursor.fetchall():
        print(f"   ID: {r[0]}, Topic: {r[1]}, Score: {r[2]}%, Percentage: {r[3]}%, Date: {r[4]}")
    
    conn.close()
    
    print("\n" + "="*60)
    if total_count == 0:
        print("🔴 SOLUTION: Take a quiz first! Then refresh dashboard.")
    elif total_count > 0 and len(results) == 0:
        print("🟡 ISSUE: You have quiz results but they are older than 7 days.")
        print("   Take a NEW quiz today to see data in the chart.")
    else:
        print("🟢 Data exists! Chart should display if frontend is working.")

if __name__ == '__main__':
    debug_chart_data()