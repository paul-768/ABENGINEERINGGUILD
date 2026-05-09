import unittest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, QuizResult, Topic
from app.scoreboard.analytics import get_user_rank, get_scoreboard_data

class ScoreboardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with self.app.app_context():
            db.create_all()
            
            # Create test users
            users = [
                User(name='User 1', email='user1@example.com'),
                User(name='User 2', email='user2@example.com'),
                User(name='User 3', email='user3@example.com')
            ]
            
            for user in users:
                user.set_password('password123')
            
            db.session.add_all(users)
            db.session.commit()
            
            # Create test topic
            topic = Topic(name='Test Topic')
            db.session.add(topic)
            db.session.commit()
            
            # Create test quiz results
            now = datetime.utcnow()
            quiz_results = [
                # User 1: Average 80%
                QuizResult(user_id=1, topic_id=1, score=70, total_questions=10, completed_at=now - timedelta(days=3)),
                QuizResult(user_id=1, topic_id=1, score=90, total_questions=10, completed_at=now - timedelta(days=1)),
                
                # User 2: Average 60%
                QuizResult(user_id=2, topic_id=1, score=50, total_questions=10, completed_at=now - timedelta(days=2)),
                QuizResult(user_id=2, topic_id=1, score=70, total_questions=10, completed_at=now - timedelta(days=1)),
                
                # User 3: Average 40% (only one quiz)
                QuizResult(user_id=3, topic_id=1, score=40, total_questions=10, completed_at=now - timedelta(days=1))
            ]
            
            db.session.add_all(quiz_results)
            db.session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_get_scoreboard_data(self):
        with self.app.app_context():
            data = get_scoreboard_data()
            
            # Should return all users ordered by average score
            self.assertEqual(len(data), 3)
            self.assertEqual(data[0].name, 'User 1')  # Highest average
            self.assertEqual(data[1].name, 'User 2')  # Middle average
            self.assertEqual(data[2].name, 'User 3')  # Lowest average
            
            # Check averages
            self.assertAlmostEqual(data[0].avg_score, 80.0)
            self.assertAlmostEqual(data[1].avg_score, 60.0)
            self.assertAlmostEqual(data[2].avg_score, 40.0)
    
    def test_get_user_rank(self):
        with self.app.app_context():
            # User 1 should be rank 1
            rank = get_user_rank(1)
            self.assertEqual(rank, 1)
            
            # User 2 should be rank 2
            rank = get_user_rank(2)
            self.assertEqual(rank, 2)
            
            # User 3 should be rank 3
            rank = get_user_rank(3)
            self.assertEqual(rank, 3)
    
    def test_filtered_scoreboard(self):
        with self.app.app_context():
            # Test with start date (only include recent results)
            start_date = datetime.utcnow().date() - timedelta(days=2)
            data = get_scoreboard_data(start_date)
            
            # Should still return all users
            self.assertEqual(len(data), 3)

if __name__ == '__main__':
    unittest.main()