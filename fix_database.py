# fix_database.py - COMPLETE DATABASE FIX
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Topic, Question, QuizResult, Post, Conversation, Message, Notification

def create_fresh_database():
    print("🔧 CREATING FRESH DATABASE...")
    print(f"📁 Working in: {os.getcwd()}")
    
    # Create app and push context
    app = create_app()
    
    with app.app_context():
        try:
            # Drop all tables and recreate
            print("🔄 Dropping and recreating all tables...")
            db.drop_all()
            db.create_all()
            print("✓ All tables created successfully")
            
            # Create admin user
            print("👤 Creating admin user...")
            admin = User(
                name="Admin User",
                email="admin@abequest.com",
                is_admin=True
            )
            admin.set_password("admin123")
            db.session.add(admin)
            
            # Create default topics based on your areas
            print("📚 Creating default topics...")
            topics_data = [
                {"name": "AREA I", "description": "Agricultural Power and Machinery", "icon": "fas fa-tractor"},
                {"name": "AREA II", "description": "Soil and Water Conservation", "icon": "fas fa-water"},
                {"name": "AREA III", "description": "Farm Structures and Environmental Control", "icon": "fas fa-building"},
                {"name": "Engineering Mathematics", "description": "Engineering Mathematics and Calculations", "icon": "fas fa-calculator"},
                {"name": "PAES Standards", "description": "Philippine Agricultural Engineering Standards", "icon": "fas fa-file-alt"}
            ]
            
            for topic_data in topics_data:
                topic = Topic(
                    name=topic_data["name"],
                    description=topic_data["description"],
                    icon=topic_data["icon"]
                )
                db.session.add(topic)
            
            # Create sample questions for each topic
            print("❓ Creating sample questions...")
            sample_questions = [
                {
                    "topic": "AREA I",
                    "question": "What is the primary function of a tractor in agriculture?",
                    "options": {
                        "A": "Soil preparation and cultivation",
                        "B": "Harvesting crops",
                        "C": "Irrigation management",
                        "D": "Pest control"
                    },
                    "correct": "A",
                    "explanation": "Tractors are mainly used for soil preparation and cultivation tasks."
                },
                {
                    "topic": "AREA II",
                    "question": "Which soil conservation method involves planting along contour lines?",
                    "options": {
                        "A": "Terracing",
                        "B": "Contour farming",
                        "C": "Crop rotation",
                        "D": "Mulching"
                    },
                    "correct": "B",
                    "explanation": "Contour farming involves planting along contour lines to reduce soil erosion."
                },
                {
                    "topic": "AREA III",
                    "question": "What is the purpose of ventilation in farm structures?",
                    "options": {
                        "A": "Temperature control",
                        "B": "Moisture reduction",
                        "C": "Air quality improvement",
                        "D": "All of the above"
                    },
                    "correct": "D",
                    "explanation": "Ventilation serves multiple purposes including temperature control, moisture reduction, and air quality improvement."
                },
                {
                    "topic": "Engineering Mathematics",
                    "question": "What is the integral of 2x dx?",
                    "options": {
                        "A": "x²",
                        "B": "2x²",
                        "C": "x² + C",
                        "D": "2x² + C"
                    },
                    "correct": "C",
                    "explanation": "The integral of 2x dx is x² + C, where C is the constant of integration."
                },
                {
                    "topic": "PAES Standards",
                    "question": "What does PAES stand for?",
                    "options": {
                        "A": "Philippine Agricultural Engineering Standards",
                        "B": "Philippine Agricultural Equipment Specifications",
                        "C": "Philippine Agricultural Engineering System",
                        "D": "Philippine Agricultural Equipment Standards"
                    },
                    "correct": "A",
                    "explanation": "PAES stands for Philippine Agricultural Engineering Standards."
                }
            ]
            
            # Get topic objects
            topic_objs = {topic.name: topic for topic in Topic.query.all()}
            
            for q_data in sample_questions:
                topic_obj = topic_objs.get(q_data["topic"])
                if topic_obj:
                    question = Question(
                        topic_id=topic_obj.id,
                        question_text=q_data["question"],
                        option_a=q_data["options"]["A"],
                        option_b=q_data["options"]["B"],
                        option_c=q_data["options"]["C"],
                        option_d=q_data["options"]["D"],
                        correct_answer=q_data["correct"],
                        explanation=q_data["explanation"],
                        difficulty="medium"
                    )
                    db.session.add(question)
            
            # Commit all changes
            db.session.commit()
            
            # Verify creation
            user_count = User.query.count()
            topic_count = Topic.query.count()
            question_count = Question.query.count()
            
            print("✅ DATABASE CREATED SUCCESSFULLY!")
            print(f"📊 File: data/quizzes.db")
            print(f"👥 Users: {user_count}")
            print(f"📖 Topics: {topic_count}")
            print(f"❓ Questions: {question_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating database: {e}")
            db.session.rollback()
            return False

def check_database_status():
    """Check current database status"""
    app = create_app()
    
    with app.app_context():
        try:
            # Try to query each main table
            tables = {
                'User': User,
                'Topic': Topic,
                'Question': Question,
                'Post': Post,
                'Conversation': Conversation
            }
            
            print("🔍 CHECKING DATABASE STATUS...")
            for table_name, model in tables.items():
                try:
                    count = model.query.count()
                    print(f"✓ {table_name}: {count} records")
                except Exception as e:
                    print(f"✗ {table_name}: Table missing or error - {e}")
                    
        except Exception as e:
            print(f"❌ Database connection error: {e}")

if __name__ == "__main__":
    print("🚀 AB ENGINEERING GUILD - DATABASE SETUP")
    print("=" * 50)
    
    # Check current status first
    check_database_status()
    
    print("\n" + "=" * 50)
    response = input("\nDo you want to create a fresh database? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n" + "=" * 50)
        success = create_fresh_database()
        
        if success:
            print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("\n🚀 You can now start your application:")
            print("   python run.py")
            print("\n🔑 Login with:")
            print("   Email: admin@abequest.com")
            print("   Password: admin123")
        else:
            print("\n❌ SETUP FAILED!")
            print("Please check the error messages above.")
    else:
        print("Operation cancelled.")