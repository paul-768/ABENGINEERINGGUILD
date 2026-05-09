# fix_db_column.py
import sqlite3

print("Connecting to database...")
conn = sqlite3.connect('data/quizzes.db')
cursor = conn.cursor()

# Check current columns
cursor.execute("PRAGMA table_info(material_link)")
columns = [col[1] for col in cursor.fetchall()]
print(f"Current columns: {columns}")

# Add material_id column if missing
if 'material_id' not in columns:
    print("Adding material_id column...")
    cursor.execute("ALTER TABLE material_link ADD COLUMN material_id INTEGER DEFAULT 0")
    conn.commit()
    print("✅ Added material_id column")
else:
    print("material_id column already exists")

# Verify column was added
cursor.execute("PRAGMA table_info(material_link)")
print("\nFinal columns:")
for col in cursor.fetchall():
    print(f"  - {col[1]} ({col[2]})")

conn.close()
print("\nDone! You can now restart your Flask server.")