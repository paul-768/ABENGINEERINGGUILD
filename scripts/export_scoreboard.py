#!/usr/bin/env python3
import os
import sys
import csv
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app, db
from app.models import User, QuizResult
from sqlalchemy import func

def export_scoreboard():
    app = create_app()
    
    with app.app_context():
        # Get scoreboard data
        scoreboard_data = db.session.query(
            User.id,
            User.name,
            func.count(QuizResult.id).label('quiz_count'),
            func.avg(QuizResult.score).label('avg_score'),
            func.max(QuizResult.completed_at).label('last_quiz_date')
        ).join(QuizResult, User.id == QuizResult.user_id)\
         .group_by(User.id)\
         .order_by(func.avg(QuizResult.score).desc())\
         .all()
        
        # Prepare data for CSV
        data = []
        for i, student in enumerate(scoreboard_data, 1):
            data.append({
                'Rank': i,
                'Student Name': student.name,
                'Quizzes Taken': student.quiz_count,
                'Average Score': f"{student.avg_score:.2f}%",
                'Last Activity': student.last_quiz_date.strftime('%Y-%m-%d') if student.last_quiz_date else 'Never'
            })
        
        # Create exports directory if it doesn't exist
        export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(export_dir, f'scoreboard_export_{timestamp}.csv')
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['Rank', 'Student Name', 'Quizzes Taken', 'Average Score', 'Last Activity']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"Scoreboard exported to {filename}")

if __name__ == '__main__':
    export_scoreboard()