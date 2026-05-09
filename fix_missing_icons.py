# fix_missing_icons.py
from app import create_app, db
from app.models import Achievement

app = create_app()

with app.app_context():
    print("=" * 60)
    print("FIXING MISSING ACHIEVEMENT ICONS")
    print("=" * 60)
    
    # Find all achievements with missing or empty icons
    missing_icons = Achievement.query.filter(
        (Achievement.icon.is_(None)) | 
        (Achievement.icon == '') | 
        (Achievement.icon == 'fas fa-trophy')
    ).all()
    
    print(f"\nFound {len(missing_icons)} achievements with missing/default icons\n")
    
    # Define icons for all achievements
    icon_fixes = {
        # Quiz Category
        'First Step': 'fas fa-flag-checkered',
        'Getting Started': 'fas fa-rocket',
        'Quiz Enthusiast': 'fas fa-clipboard-list',
        'Dedicated Learner': 'fas fa-graduation-cap',
        'Quiz Master': 'fas fa-crown',
        'Quiz Legend': 'fas fa-star-of-life',
        'Perfect Score': 'fas fa-check-double',
        'Perfect x3': 'fas fa-medal',
        'Perfect x5': 'fas fa-trophy',
        'Perfect Streak': 'fas fa-crown',
        'High Achiever': 'fas fa-chart-line',
        'Top Performer': 'fas fa-chart-line',
        'Elite Scorer': 'fas fa-crown',
        'Question Warrior': 'fas fa-brain',
        'Knowledge Seeker': 'fas fa-book-reader',
        'Question Master': 'fas fa-database',
        'Walking Encyclopedia': 'fas fa-university',
        'Time Keeper': 'fas fa-hourglass-half',
        'Study Warrior': 'fas fa-clock',
        'Dedicated Scholar': 'fas fa-user-graduate',
        
        # Streak Category
        '3-Day Streak': 'fas fa-calendar-day',
        '7-Day Streak': 'fas fa-calendar-week',
        '14-Day Streak': 'fas fa-calendar-alt',
        '30-Day Streak': 'fas fa-calendar-check',
        '60-Day Streak': 'fas fa-fire',
        '100-Day Streak': 'fas fa-star',
        'Weekend Warrior': 'fas fa-calendar-weekend',
        'Month Master': 'fas fa-calendar-month',
        'Semester Scholar': 'fas fa-calendar-plus',
        'Year Round': 'fas fa-calendar-year',
        
        # AREA I - Farm Machinery
        'Farm Apprentice': 'fas fa-tractor',
        'Farm Hand': 'fas fa-tractor',
        'Machinery Operator': 'fas fa-tractor',
        'Farm Machinery Expert': 'fas fa-certificate',
        'Farm Machinery Starter': 'fas fa-play',
        'Farm Machinery Enthusiast': 'fas fa-heart',
        'Farm Machinery Master': 'fas fa-crown',
        'Farm Machinery Perfectionist': 'fas fa-star',
        'Farm Equipment Guru': 'fas fa-database',
        'Machinery Champion': 'fas fa-trophy',
        
        # AREA II - Soil & Water
        'Soil Scout': 'fas fa-tint',
        'Water Watcher': 'fas fa-water',
        'Soil Scientist': 'fas fa-flask',
        'Water Resource Expert': 'fas fa-certificate',
        'Soil Sampler': 'fas fa-play',
        'Irrigation Specialist': 'fas fa-sprinkler',
        'Watershed Warrior': 'fas fa-mountain',
        'Soil Conservationist': 'fas fa-star',
        'Water Management Master': 'fas fa-database',
        'Soil & Water Champion': 'fas fa-trophy',
        
        # AREA III - Post-Harvest
        'Harvester Helper': 'fas fa-boxes',
        'Grain Handler': 'fas fa-warehouse',
        'Post-Harvest Pro': 'fas fa-industry',
        'Storage Specialist': 'fas fa-certificate',
        'Drying Expert': 'fas fa-sun',
        'Milling Master': 'fas fa-cogs',
        'Processing Pro': 'fas fa-microchip',
        'Quality Controller': 'fas fa-star',
        'Post-Harvest Guru': 'fas fa-database',
        'Post-Harvest Champion': 'fas fa-trophy',
        
        # Engineering Math
        'Math Beginner': 'fas fa-calculator',
        'Equation Solver': 'fas fa-square-root-variable',
        'Math Wizard': 'fas fa-hat-wizard',
        'Calculus Master': 'fas fa-chart-line',
        'Number Cruncher': 'fas fa-play',
        'Formula Finder': 'fas fa-gear',
        'Algebraic Ace': 'fas fa-crown',
        'Mathlete': 'fas fa-star',
        'Engineering Math Expert': 'fas fa-database',
        'Math Champion': 'fas fa-trophy',
        
        # PAES Standards
        'PAES Reader': 'fas fa-file-alt',
        'Standard Seeker': 'fas fa-book',
        'Code Enforcer': 'fas fa-gavel',
        'PAES Expert': 'fas fa-certificate',
        'Standard Scout': 'fas fa-play',
        'Code Collector': 'fas fa-folder-open',
        'Regulation Reader': 'fas fa-scale-balanced',
        'PAES Perfectionist': 'fas fa-star',
        'PAES Master': 'fas fa-database',
        'PAES Champion': 'fas fa-trophy',
        
        # Social
        'First Friend': 'fas fa-user-plus',
        'Social Butterfly': 'fas fa-butterfly',
        'Community Builder': 'fas fa-users',
        'Networking Pro': 'fas fa-network-wired',
        'First Post': 'fas fa-pen',
        'Active Contributor': 'fas fa-pen-alt',
        'Engaged Citizen': 'fas fa-newspaper',
        'First Comment': 'fas fa-comment',
        'Discussion Starter': 'fas fa-comments',
        'Community Leader': 'fas fa-chalkboard-user',
        
        # Special
        'All-Rounder': 'fas fa-globe',
        'True Scholar': 'fas fa-graduation-cap',
        'Renaissance Engineer': 'fas fa-microscope',
        'Board Exam Ready': 'fas fa-clipboard',
        'Top 50': 'fas fa-ranking-star',
        'Top 25': 'fas fa-medal',
        'Top 10': 'fas fa-trophy',
        'Top 5': 'fas fa-crown',
        'Number 1': 'fas fa-star-of-life',
        'Grand Master': 'fas fa-gem'
    }
    
    # Update each achievement
    updated_count = 0
    for achievement in missing_icons:
        if achievement.name in icon_fixes:
            old_icon = achievement.icon
            achievement.icon = icon_fixes[achievement.name]
            print(f"  ✓ {achievement.name}: '{old_icon}' → '{achievement.icon}'")
            updated_count += 1
        else:
            # Set a default icon
            achievement.icon = 'fas fa-trophy'
            print(f"  ⚠ {achievement.name}: set to default 'fas fa-trophy'")
            updated_count += 1
    
    db.session.commit()
    
    print(f"\n{'=' * 60}")
    print(f"✅ Updated {updated_count} achievements with icons!")
    
    # Verify
    still_missing = Achievement.query.filter(
        (Achievement.icon.is_(None)) | 
        (Achievement.icon == '')
    ).count()
    
    if still_missing > 0:
        print(f"\n⚠ Warning: {still_missing} achievements still have no icon")
    else:
        print("\n✓ All achievements now have icons!")
    
    print("=" * 60)