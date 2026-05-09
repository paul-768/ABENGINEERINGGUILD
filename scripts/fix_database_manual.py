# fix_database_manual.py
import sqlite3
import os

def fix_database_manual():
    db_path = os.path.join(os.path.dirname(__file__), 'data', 'quizzes.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding missing columns to database...")
        
        # Add icon column to topic table
        try:
            cursor.execute("ALTER TABLE topic ADD COLUMN icon VARCHAR(50) DEFAULT 'fas fa-folder'")
            print("✓ Added icon column to topic table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Note: {e}")
        
        # Add columns to post table
        try:
            cursor.execute("ALTER TABLE post ADD COLUMN media_file VARCHAR(255)")
            print("✓ Added media_file column to post table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Note: {e}")
        
        try:
            cursor.execute("ALTER TABLE post ADD COLUMN media_type VARCHAR(20)")
            print("✓ Added media_type column to post table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Note: {e}")
        
        try:
            cursor.execute("ALTER TABLE post ADD COLUMN view_count INTEGER DEFAULT 0")
            print("✓ Added view_count column to post table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Note: {e}")
        
        try:
            cursor.execute("ALTER TABLE post ADD COLUMN parent_post_id INTEGER")
            print("✓ Added parent_post_id column to post table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e):
                print(f"Note: {e}")
        
        # Create friend_request table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friend_request (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES user (id),
                FOREIGN KEY (receiver_id) REFERENCES user (id)
            )
        ''')
        print("✓ Created friend_request table")
        
        # Add foreign key constraint manually (without name to avoid the error)
        try:
            cursor.execute('''
                PRAGMA foreign_keys=off;
                BEGIN TRANSACTION;
                CREATE TABLE post_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200),
                    content TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    topic_id INTEGER,
                    post_type VARCHAR(20) DEFAULT 'discussion',
                    media_file VARCHAR(255),
                    media_type VARCHAR(20),
                    view_count INTEGER DEFAULT 0,
                    parent_post_id INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES user (id),
                    FOREIGN KEY (topic_id) REFERENCES topic (id),
                    FOREIGN KEY (parent_post_id) REFERENCES post (id)
                );
                INSERT INTO post_new SELECT * FROM post;
                DROP TABLE post;
                ALTER TABLE post_new RENAME TO post;
                COMMIT;
                PRAGMA foreign_keys=on;
            ''')
            print("✓ Updated post table with foreign key constraints")
        except sqlite3.Error as e:
            print(f"Note: Could not add foreign key constraint: {e}")
        
        conn.commit()
        print("\n✓ Database updated successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    fix_database_manual()