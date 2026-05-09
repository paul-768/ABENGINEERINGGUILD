# clean_reset.py
import os
import shutil
from app import create_app, db

def clean_reset():
    print("🧹 Performing clean database reset...")
    
    # Delete database file
    db_path = 'data/quizzes.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✓ Deleted old database")
    
    # Delete migrations folder if it exists
    if os.path.exists('migrations'):
        shutil.rmtree('migrations')
        print("✓ Deleted migrations folder")
    
    # Create new app and database
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Created all database tables")
        
        # Create default admin user
        from app.models import User
        admin = User.query.filter_by(email='admin@abequest.com').first()
        if not admin:
            admin = User(
                name='Admin', 
                email='admin@abequest.com', 
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Created admin user (email: admin@abequest.com, password: admin123)")
        
        # Create some sample topics
        from app.models import Topic
        if Topic.query.count() == 0:
            sample_topics = [
                {'name': 'Farm Machinery', 'description': 'Agricultural equipment and machinery'},
                {'name': 'Soil & Water Management', 'description': 'Soil conservation and water resources'},
                {'name': 'Post-Harvest Technology', 'description': 'Crop processing and storage'},
                {'name': 'Environmental Engineering', 'description': 'Environmental systems and management'},
                {'name': 'PAES Standards', 'description': 'Philippine Agricultural Engineering Standards'},
            ]
            
            for topic_data in sample_topics:
                topic = Topic(
                    name=topic_data['name'],
                    description=topic_data['description']
                )
                db.session.add(topic)
            
            db.session.commit()
            print("✓ Created sample topics")
    
    print("✅ Clean reset completed successfully!")
    print("🚀 You can now run: python run.py")

if __name__ == '__main__':
    clean_reset()