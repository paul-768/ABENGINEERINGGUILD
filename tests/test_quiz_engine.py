import unittest
from app import create_app, db
from app.models import Question
from app.quiz.engine import generate_quiz, calculate_score

class QuizEngineTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with self.app.app_context():
            db.create_all()
            
            # Create test questions
            questions = [
                Question(
                    topic_id=1,
                    question_text="Test question 1",
                    option_a="Option A",
                    option_b="Option B",
                    option_c="Option C",
                    option_d="Option D",
                    correct_answer="A"
                ),
                Question(
                    topic_id=1,
                    question_text="Test question 2",
                    option_a="Option A",
                    option_b="Option B",
                    option_c="Option C",
                    option_d="Option D",
                    correct_answer="B"
                ),
                Question(
                    topic_id=2,
                    question_text="Test question 3",
                    option_a="Option A",
                    option_b="Option B",
                    option_c="Option C",
                    option_d="Option D",
                    correct_answer="C"
                )
            ]
            
            db.session.add_all(questions)
            db.session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_generate_quiz(self):
        with self.app.app_context():
            # Test generating quiz for topic 1
            questions = generate_quiz(1, 2)
            self.assertEqual(len(questions), 2)
            
            # All questions should be from topic 1
            for question in questions:
                self.assertEqual(question.topic_id, 1)
            
            # Test requesting more questions than available
            questions = generate_quiz(1, 10)
            self.assertEqual(len(questions), 2)  # Only 2 questions available for topic 1
    
    def test_calculate_score(self):
        with self.app.app_context():
            questions = Question.query.filter_by(topic_id=1).all()
            
            # Test perfect score
            answers = {
                str(questions[0].id): "A",
                str(questions[1].id): "B"
            }
            score, correct, total = calculate_score(questions, answers)
            self.assertEqual(score, 100.0)
            self.assertEqual(correct, 2)
            self.assertEqual(total, 2)
            
            # Test 50% score
            answers = {
                str(questions[0].id): "A",
                str(questions[1].id): "A"  # Wrong answer
            }
            score, correct, total = calculate_score(questions, answers)
            self.assertEqual(score, 50.0)
            self.assertEqual(correct, 1)
            self.assertEqual(total, 2)
            
            # Test no answers
            answers = {}
            score, correct, total = calculate_score(questions, answers)
            self.assertEqual(score, 0.0)
            self.assertEqual(correct, 0)
            self.assertEqual(total, 2)

if __name__ == '__main__':
    unittest.main()