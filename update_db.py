# update_db.py
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
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
            print(f'Added column: {col_name}')
        except Exception as e:
            if 'duplicate column' in str(e).lower():
                print(f'Column {col_name} already exists')
            else:
                print(f'Error adding {col_name}: {e}')
    
    db.session.commit()
    print('Database updated successfully!')