#!/usr/bin/env python3
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import Topic

app = create_app()

def migrate_database():
    """Migrate the database to add new columns"""
    with app.app_context():
        try:
            # Add material_type column to study_material table
            db.engine.execute('''
                ALTER TABLE study_material 
                ADD COLUMN material_type VARCHAR(50) DEFAULT 'pdf'
            ''')
            print("✓ Added material_type column to study_material table")
            
            # Update topic names to new format
            topic_updates = {
                "Farm Machinery": "AREA I",
                "Soil & Water Management": "AREA II", 
                "Post-Harvest Technology": "AREA III",
                "Environmental Engineering": "Engineering Mathematics",
                "PAES Standards": "PAES Standards"
            }
            
            for old_name, new_name in topic_updates.items():
                topic = Topic.query.filter_by(name=old_name).first()
                if topic:
                    topic.name = new_name
                    print(f"✓ Updated topic: {old_name} → {new_name}")
            
            db.session.commit()
            print("✓ Database migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration error: {e}")
            # If ALTER TABLE fails (like if column already exists), continue
            if "duplicate column name" in str(e).lower():
                print("✓ Column already exists, continuing...")
                db.session.commit()

if __name__ == '__main__':
    print("Starting database migration...")
    migrate_database()