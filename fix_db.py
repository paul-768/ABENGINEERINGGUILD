# fix_db.py
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Updating database...")
    
    # Add missing columns to achievement table
    columns = [
        ('requirement_type', "VARCHAR(50) DEFAULT 'quiz_count'"),
        ('requirement_value', 'INTEGER DEFAULT 0'),
        ('requirement_extra', 'VARCHAR(100)'),
        ('badge_color', "VARCHAR(20) DEFAULT 'yellow'"),
        ('display_order', 'INTEGER DEFAULT 0'),
        ('is_hidden', 'BOOLEAN DEFAULT 0')
    ]
    
    for col_name, col_type in columns:
        try:
            db.session.execute(text(f'ALTER TABLE achievement ADD COLUMN {col_name} {col_type}'))
            print(f'✓ Added column: {col_name}')
        except Exception as e:
            if 'duplicate column name' in str(e).lower():
                print(f'✓ Column {col_name} already exists')
            else:
                print(f'⚠ {col_name}: {e}')
    
    db.session.commit()
    print("\nDatabase update complete!")
    
    # Check if achievements exist
    from app.models import Achievement
    count = Achievement.query.count()
    print(f"Achievements in database: {count}")
    
    if count == 0:
        print("Running seed...")
        import subprocess
        subprocess.run(["python", "seed_achievements.py"])