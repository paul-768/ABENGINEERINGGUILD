# test_achievements_api.py
from app import create_app
from app.models import Achievement, UserAchievement
from flask_login import current_user

app = create_app()

with app.app_context():
    print("\n=== Testing Achievements API ===\n")
    
    # Test getting all achievements
    try:
        achievements = Achievement.query.all()
        print(f"Found {len(achievements)} achievements in database")
        for a in achievements[:5]:
            print(f"  - {a.name} (category: {a.category})")
    except Exception as e:
        print(f"Error loading achievements: {e}")
    
    # Test the stats query that the API uses
    from sqlalchemy import func
    
    try:
        stats = {
            'total_achievements': Achievement.query.count(),
            'unlocked_count': UserAchievement.query.filter_by(user_id=1).count() if UserAchievement.query.first() else 0,
            'total_points': 0
        }
        print(f"\nStats: {stats}")
    except Exception as e:
        print(f"Error calculating stats: {e}")