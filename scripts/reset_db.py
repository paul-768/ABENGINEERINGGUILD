#!/usr/bin/env python3
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User, Topic, Question, StudyMaterial, PAESStandard
import json

app = create_app()

def reset_database():
    """Completely reset the database with new schema"""
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Creating new tables...")
        db.create_all()
        
        # Create admin user
        admin = User(name='Admin', email='admin@agriquest.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create topics with new names
        topics_data = [
            {"name": "AREA I", "description": "Farm Machinery and Equipment - Study of agricultural machinery and equipment used in farming operations"},
            {"name": "AREA II", "description": "Soil and Water Conservation Engineering - Principles and practices of soil conservation and water management in agriculture"},
            {"name": "AREA III", "description": "Post-Harvest and Processing Engineering - Technologies and methods for handling, processing, and preserving agricultural products after harvest"},
            {"name": "Engineering Mathematics", "description": "Mathematical Principles for Engineering Applications - Application of mathematical concepts to solve engineering problems"},
            {"name": "PAES Standards", "description": "Philippine Agricultural Engineering Standards and specifications - Official standards for agricultural machinery, structures, and practices"}
        ]
        
        for topic_data in topics_data:
            topic = Topic(**topic_data)
            db.session.add(topic)
        
        db.session.commit()
        
        # Add sample study materials
        topics = Topic.query.all()
        for topic in topics:
            material = StudyMaterial(
                topic_id=topic.id,
                title=f"Introduction to {topic.name}",
                content=f"This is a comprehensive guide to {topic.name}. Learn the fundamentals and advanced concepts.",
                file_path=None,
                material_type="pdf"
            )
            db.session.add(material)
        
        # Add PAES standards
        paes_standards = [
            {"code": "PAES 101", "title": "Agricultural Machinery - Classification", "description": "Classification of agricultural machinery and equipment"},
            {"code": "PAES 102", "title": "Agricultural Machinery - Testing", "description": "Code of practice for testing agricultural machinery and equipment"},
            {"code": "PAES 103", "title": "Agricultural Machinery - Safety", "description": "Safety requirements for agricultural machinery and equipment"},
            {"code": "PAES 201", "title": "Soil and Water Management", "description": "Standards for soil and water conservation practices"},
            {"code": "PAES 301", "title": "Postharvest Facilities", "description": "Standards for postharvest facilities and equipment"},
        ]
        
        for paes_data in paes_standards:
            paes = PAESStandard(**paes_data)
            db.session.add(paes)
        
        db.session.commit()
        print("✓ Database reset completed successfully!")
        print("✓ New topics created:")
        for topic in Topic.query.all():
            print(f"  - {topic.name}: {topic.description}")

if __name__ == '__main__':
    print("Resetting database...")
    reset_database()