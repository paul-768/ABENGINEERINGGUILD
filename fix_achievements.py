# fix_achievements.py
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check if columns exist and add them if not
    try:
        # Get existing columns
        result = db.session.execute(text("PRAGMA table_info(achievement)"))
        existing_columns = [row[1] for row in result.fetchall()]
        
        columns_to_add = {
            'requirement_type': "VARCHAR(50) DEFAULT 'quiz_count'",
            'requirement_value': 'INTEGER DEFAULT 0',
            'requirement_extra': 'VARCHAR(100)',
            'badge_color': "VARCHAR(20) DEFAULT 'yellow'",
            'display_order': 'INTEGER DEFAULT 0',
            'is_hidden': 'BOOLEAN DEFAULT 0'
        }
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                try:
                    db.session.execute(text(f'ALTER TABLE achievement ADD COLUMN {col_name} {col_type}'))
                    print(f'✓ Added column: {col_name}')
                except Exception as e:
                    print(f'✗ Error adding {col_name}: {e}')
            else:
                print(f'✓ Column already exists: {col_name}')
        
        db.session.commit()
        print('✅ Database columns updated!')
        
    except Exception as e:
        print(f'Error: {e}')
        db.session.rollback()