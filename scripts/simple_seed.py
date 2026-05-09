import json
import sqlite3
import os
from datetime import datetime

def simple_seed_questions():
    # Path to your database
    db_path = os.path.join('data', 'quizzes.db')
    
    # Load questions from JSON file
    with open('data/seed/questions_seed.json', 'r') as f:
        questions_data = json.load(f)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create topics if they don't exist
    topic_names = {
        1: "PAES Standards",
        2: "Soil & Water Management", 
        3: "Farm Machinery",
        4: "Post-Harvest Technology",
        5: "Environmental Engineering"
    }
    
    for topic_id, topic_name in topic_names.items():
        # Check if topic exists
        cursor.execute("SELECT id FROM topic WHERE id = ?", (topic_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO topic (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                (topic_id, topic_name, f"Questions about {topic_name}", datetime.utcnow())
            )
            print(f"Created topic: {topic_name}")
    
    # Add questions to database
    added_count = 0
    skipped_count = 0
    
    for q_data in questions_data:
        # Check if question already exists by text
        cursor.execute("SELECT id FROM question WHERE question_text = ?", (q_data['question_text'],))
        if not cursor.fetchone():
            cursor.execute(
                """INSERT INTO question 
                (topic_id, question_text, option_a, option_b, option_c, option_d, correct_answer, explanation, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    q_data['topic_id'],
                    q_data['question_text'],
                    q_data['option_a'],
                    q_data['option_b'],
                    q_data['option_c'],
                    q_data['option_d'],
                    q_data['correct_answer'],
                    q_data.get('explanation', ''),
                    datetime.utcnow()
                )
            )
            added_count += 1
        else:
            skipped_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Successfully seeded {added_count} questions")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} existing questions")

if __name__ == '__main__':
    simple_seed_questions()