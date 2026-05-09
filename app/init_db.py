import os
import sys
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Topic, Question, StudyMaterial, PAESStandard
from app import create_app, db

def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✅ Database initialized.")

if __name__ == "__main__":
    main()

def init_database():
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user
        if not User.query.filter_by(email='admin@agriquest.com').first():
            admin = User(name='Admin', email='admin@agriquest.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Admin user created")
        
        # Create topics if they don't exist
        if Topic.query.count() == 0:
            seed_path = os.path.join('data', 'seed')
            
            # Create seed directory if it doesn't exist
            os.makedirs(seed_path, exist_ok=True)
            
            # Create default topics if seed file doesn't exist
            topics_file = os.path.join(seed_path, 'topics_seed.json')
            if not os.path.exists(topics_file):
                topics_data = [
                    {"name": "Farm Machinery", "description": "Study of agricultural machinery and equipment used in farming operations."},
                    {"name": "Soil & Water Management", "description": "Principles and practices of soil conservation and water management in agriculture."},
                    {"name": "Post-Harvest Technology", "description": "Technologies and methods for handling, processing, and preserving agricultural products after harvest."},
                    {"name": "Environmental Engineering", "description": "Application of engineering principles to environmental protection and resource management."},
                    {"name": "PAES Standards", "description": "Philippine Agricultural Engineering Standards and specifications."}
                    {"name": "Engineering Economics", "description": "Economic analysis and decision-making for engineering projects"}
                ]
                with open(topics_file, 'w') as f:
                    json.dump(topics_data, f, indent=2)
            
            # Load topics
            with open(topics_file, 'r') as f:
                topics_data = json.load(f)
                
                for topic_data in topics_data:
                    topic = Topic(
                        name=topic_data['name'],
                        description=topic_data['description']
                    )
                    db.session.add(topic)
            
            print("✓ Topics seeded")
        
        # Create questions if they don't exist
        if Question.query.count() == 0:
            seed_path = os.path.join('data', 'seed')
            
            # Create default questions if seed file doesn't exist
            questions_file = os.path.join(seed_path, 'questions_seed.json')
            if not os.path.exists(questions_file):
                questions_data = [
                    {
                        "topic_id": 1,
                        "question_text": "What is the primary function of a tractor in farming operations?",
                        "option_a": "Soil preparation",
                        "option_b": "Harvesting",
                        "option_c": "Irrigation",
                        "option_d": "Seed planting",
                        "correct_answer": "A",
                        "explanation": "Tractors are primarily used for soil preparation tasks such as plowing, harrowing, and disking."
                    },
                    {
                        "topic_id": 1,
                        "question_text": "Which of the following is NOT a type of plow?",
                        "option_a": "Moldboard plow",
                        "option_b": "Disc plow",
                        "option_c": "Chisel plow",
                        "option_d": "Combine plow",
                        "correct_answer": "D",
                        "explanation": "There is no such thing as a combine plow. Combine refers to a harvesting machine."
                    }
                ]
                with open(questions_file, 'w') as f:
                    json.dump(questions_data, f, indent=2)
            
            # Load questions
            with open(questions_file, 'r') as f:
                questions_data = json.load(f)
                
                for question_data in questions_data:
                    question = Question(
                        topic_id=question_data['topic_id'],
                        question_text=question_data['question_text'],
                        option_a=question_data['option_a'],
                        option_b=question_data['option_b'],
                        option_c=question_data['option_c'],
                        option_d=question_data['option_d'],
                        correct_answer=question_data['correct_answer'],
                        explanation=question_data.get('explanation', '')
                    )
                    db.session.add(question)
            
            print("✓ Questions seeded")
        
        # Create sample study materials
        if StudyMaterial.query.count() == 0:
            topics = Topic.query.all()
            for topic in topics:
                material = StudyMaterial(
                    topic_id=topic.id,
                    title=f"Introduction to {topic.name}",
                    content=f"This is a comprehensive guide to {topic.name}. Learn the fundamentals and advanced concepts.",
                    file_path=f"/static/paes/{topic.name.lower().replace(' ', '_')}.pdf"
                )
                db.session.add(material)
            
            print("✓ Study materials created")
        

if __name__ == '__main__':
    init_database()