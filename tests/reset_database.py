# reset_database.py
import os
import sqlite3
from app import create_app, db

def reset_database():
    app = create_app()
    
    with app.app_context():
        # Get database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print("🔄 Resetting database...")
        
        # Close any existing connections
        db.session.close()
        
        # Drop and recreate all tables
        db.drop_all()
        db.create_all()
        
        print("✅ Database reset complete!")
        print("✅ All tables recreated with new schema")
        print("✅ Notification system ready!")

if __name__ == "__main__":
    reset_database()