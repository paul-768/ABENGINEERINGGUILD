import sqlite3
import json

conn = sqlite3.connect('data/quizzes.db')
c = conn.cursor()
c.execute('DELETE FROM question')

with open('data/seed/questions_seed.json', encoding='utf-8') as f:
    data = json.load(f)

count = 0
for q in data:
    explanation = q.get('explanation', '')
    try:
        c.execute('''INSERT INTO question 
            (topic_id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, created_at) 
            VALUES (?,?,?,?,?,?,?,?,datetime('now'))''',
            (q['topic_id'], q['question_text'], q['option_a'], q['option_b'], 
             q['option_c'], q['option_d'], q['correct_answer'], explanation))
        count += 1
    except Exception as e:
        print(f"Error on record: {e}")

conn.commit()
print(f'✓ Seeded {count} questions')
conn.close()