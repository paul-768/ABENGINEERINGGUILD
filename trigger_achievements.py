# trigger_achievements.py - Run this manually to check achievements
from app import create_app, db
from app.models import User
from app.achievements.routes import check_achievements

app = create_app()

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"Checking achievements for: {user.name}")
        # You need to make check_achievements work without request context
        # Or modify the route to accept a user_id parameter