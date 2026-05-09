from app import db
from app.models import User, Topic, Question, StudyMaterial, PAESStandard, QuizResult
import json
import os

def init_db():
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(email='admin@agriquest.com').first():
        admin = User(name='Admin', email='admin@agriquest.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    
    # Load seed data if topics table is empty
    if Topic.query.count() == 0:
        seed_path = os.path.join(os.path.dirname(__file__), '../data/seed')
        
        # Load topics
        with open(os.path.join(seed_path, 'topics_seed.json'), 'r') as f:
            topics_data = json.load(f)
            
            for topic_data in topics_data:
                topic = Topic(
                    name=topic_data['name'],
                    description=topic_data['description']
                )
                db.session.add(topic)
        
        db.session.commit()
        
        # Load questions
        with open(os.path.join(seed_path, 'questions_seed.json'), 'r') as f:
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
        
        db.session.commit()
        
    # Create some sample study materials with updated structure
    if StudyMaterial.query.count() == 0:
        topics = Topic.query.all()
        for topic in topics:
            material = StudyMaterial(
                topic_id=topic.id,
                title=f"Introduction to {topic.name}",
                content=f"This is a comprehensive guide to {topic.name}. Learn the fundamentals and advanced concepts.",
                file_path=None,  # Will be updated when actual files are uploaded
                material_type="pdf"
            )
            db.session.add(material)
        
        db.session.commit()
    
    # Create some PAES standards
    if PAESStandard.query.count() == 0:
        paes_standards = [
            {"code": "PAES 101", "title": "Agricultural Machinery - Classification", "description": "Classification of agricultural machinery and equipment"},
            {"code": "PAES 102", "title": "Agricultural Machinery - Testing", "description": "Code of practice for testing agricultural machinery and equipment"},
            {"code": "PAES 103", "title": "Agricultural Machinery - Safety", "description": "Safety requirements for agricultural machinery and equipment"},
            {"code": "PAES 201", "title": "Soil and Water Management", "description": "Standards for soil and water conservation practices"},
            {"code": "PAES 301", "title": "Postharvest Facilities", "description": "Standards for postharvest facilities and equipment"},
        ]
        
        for paes_data in paes_standards:
            paes = PAESStandard(
                code=paes_data['code'],
                title=paes_data['title'],
                description=paes_data['description'],
                file_path=None  # Will be updated when actual files are uploaded
            )
            db.session.add(paes)
        
        db.session.commit()