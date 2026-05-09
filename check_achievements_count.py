# check_achievements_count.py
from app import create_app, db
from app.models import Achievement

app = create_app()
with app.app_context():
    count = Achievement.query.count()
    print(f"Achievements in database: {count}")
    
    # Show first 10 achievements
    achievements = Achievement.query.limit(10).all()
    print("\nFirst 10 achievements:")
    for ach in achievements:
        print(f"  - {ach.name} (Category: {ach.category})")