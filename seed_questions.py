import sqlite3
import json
import os

DB_PATH = 'data/quizzes.db'

def seed_questions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if questions exist
    cursor.execute("SELECT COUNT(*) FROM question")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"✅ Already have {count} questions in database")
        conn.close()
        return
    
    # Load seed data
    with open('data/seed/questions_seed.json', 'r') as f:
        questions = json.load(f)
    
    # Insert questions
    inserted = 0
    for q in questions:
        cursor.execute("""
            INSERT INTO question (topic_id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, difficulty, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (q['topic_id'], q['question_text'], q['option_a'], q['option_b'], q['option_c'], q['option_d'], q['correct_answer'], q['explanation'], 'medium'))
        inserted += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Seeded {inserted} questions successfully!")

if __name__ == '__main__':
    seed_questions()