#!/usr/bin/env python3
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Topic

app = create_app()

def migrate_topics():
    """Update topic names in the database"""
    with app.app_context():
        try:
            # Define the topic name mappings
            topic_mappings = {
                "Farm Machinery": "AREA I",
                "Soil & Water Management": "AREA II", 
                "Post-Harvest Technology": "AREA III",
                "Environmental Engineering": "Engineering Mathematics",
                "PAES Standards": "PAES Standards"  # This one stays the same
            }
            
            # Update each topic
            for old_name, new_name in topic_mappings.items():
                topic = Topic.query.filter_by(name=old_name).first()
                if topic:
                    print(f"Updating: {old_name} → {new_name}")
                    topic.name = new_name
                else:
                    print(f"Topic not found: {old_name}")
            
            db.session.commit()
            print("✓ Topic names updated successfully!")
            
            # Verify the changes
            print("\nCurrent topics in database:")
            for topic in Topic.query.all():
                print(f"  - {topic.name}: {topic.description}")
                
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error: {e}")

if __name__ == '__main__':
    print("Starting topic migration...")
    migrate_topics()