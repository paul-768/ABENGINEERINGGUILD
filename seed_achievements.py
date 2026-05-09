#!/usr/bin/env python
"""Seed achievements data into database"""

import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Achievement

app = create_app()

def seed_achievements():
    with app.app_context():
        # Check if achievements already exist
        if Achievement.query.count() > 0:
            print(f"Already have {Achievement.query.count()} achievements. Skipping seed.")
            return
        
        # Load achievements from JSON
        json_path = os.path.join('data', 'seed', 'achievements_seed.json')
        
        if not os.path.exists(json_path):
            print(f"Error: {json_path} not found!")
            return
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        achievements = data.get('achievements', [])
        
        for ach_data in achievements:
            achievement = Achievement(
                name=ach_data['name'],
                description=ach_data['description'],
                icon=ach_data['icon'],
                points=ach_data['points'],
                category=ach_data['category'],
                requirement_type=ach_data['requirement_type'],
                requirement_value=ach_data['requirement_value'],
                requirement_extra=ach_data.get('requirement_extra'),
                badge_color=ach_data['badge_color'],
                display_order=ach_data['display_order']
            )
            db.session.add(achievement)
        
        db.session.commit()
        print(f"Successfully seeded {len(achievements)} achievements!")

if __name__ == '__main__':
    seed_achievements()