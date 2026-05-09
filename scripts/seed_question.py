import json
import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Topic, Question

def seed_questions():
    app = create_app()
    
    with app.app_context():
        # Load questions from JSON file
        with open('data/seed/questions_seed.json', 'r') as f:
            questions_data = json.load(f)
        
        # Create topics if they don't exist
        topic_names = {
            1: "PAES Standards",
            2: "Soil & Water Management", 
            3: "Farm Machinery",
            4: "Post-Harvest Technology",
            5: "Environmental Engineering"
        }
        
        for topic_id, topic_name in topic_names.items():
            # Use session.get() instead of Query.get() for SQLAlchemy 2.0 compatibility
            existing_topic = db.session.get(Topic, topic_id)
            if not existing_topic:
                topic = Topic(id=topic_id, name=topic_name, description=f"Questions about {topic_name}")
                db.session.add(topic)
        
        db.session.commit()
        
        # Add questions to database
        added_count = 0
        skipped_count = 0
        
        for q_data in questions_data:
            # Check if question already exists by text
            existing_question = Question.query.filter_by(question_text=q_data['question_text']).first()
            if not existing_question:
                question = Question(
                    topic_id=q_data['topic_id'],
                    question_text=q_data['question_text'],
                    option_a=q_data['option_a'],
                    option_b=q_data['option_b'],
                    option_c=q_data['option_c'],
                    option_d=q_data['option_d'],
                    correct_answer=q_data['correct_answer'],
                    explanation=q_data.get('explanation', ''),
                    created_at=datetime.utcnow()
                )
                db.session.add(question)
                added_count += 1
            else:
                skipped_count += 1
        
        db.session.commit()
        print(f"Successfully seeded {added_count} questions")
        if skipped_count > 0:
            print(f"Skipped {skipped_count} existing questions")

if __name__ == '__main__':
    seed_questions()