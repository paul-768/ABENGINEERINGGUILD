# update_specific_icons.py
from app import create_app, db
from app.models import Achievement

app = create_app()

with app.app_context():
    print("=" * 60)
    print("UPDATING SPECIFIC ACHIEVEMENT ICONS")
    print("=" * 60)
    
    # Define the icons to update
    icon_updates = {
        'Top 50': 'fas fa-chart-line',
        'Irrigation Specialist': 'fas fa-tint',
        'Weekend Warrior': 'fas fa-calendar-alt',
        'Month Master': 'fas fa-calendar-alt',
        'Year Round': 'fas fa-calendar-alt',
        'Social Butterfly': 'fas fa-users'
    }
    
    # Update each achievement
    for name, new_icon in icon_updates.items():
        achievement = Achievement.query.filter_by(name=name).first()
        if achievement:
            old_icon = achievement.icon
            achievement.icon = new_icon
            print(f"  ✓ {name}: '{old_icon}' → '{new_icon}'")
        else:
            print(f"  ✗ {name}: Not found in database")
    
    db.session.commit()
    
    print("\n" + "=" * 60)
    print("✅ Icons updated! Restart Flask and refresh the page.")
    print("=" * 60)