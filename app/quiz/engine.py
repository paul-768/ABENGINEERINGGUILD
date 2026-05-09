from app.models import Question
import random
from app.analytics.calculator import get_user_performance_data

def generate_quiz(topic_id, num_questions=10):
    """Generate a quiz with random questions from a topic"""
    questions = Question.query.filter_by(topic_id=topic_id).all()
    
    if not questions:
        return []
    
    # Ensure we don't request more questions than available
    num_questions = min(num_questions, len(questions))
    
    if len(questions) > num_questions:
        return random.sample(questions, num_questions)
    else:
        return questions

def generate_random_quiz(num_questions=10):
    """Generate a random quiz with questions from all topics"""
    questions = Question.query.all()
    
    if not questions:
        return []
    
    # Ensure we don't request more questions than available
    num_questions = min(num_questions, len(questions))
    
    if len(questions) > num_questions:
        return random.sample(questions, num_questions)
    else:
        return questions

def calculate_score(questions, answers):
    """Calculate quiz score based on answers"""
    correct = 0
    total = len(questions)
    
    print(f"DEBUG - calculate_score: Total questions: {total}")
    print(f"DEBUG - Answers received: {answers}")
    
    for question in questions:
        user_answer = answers.get(str(question.id))
        correct_answer = question.correct_answer
        
        print(f"DEBUG - Question {question.id}: User={user_answer}, Correct={correct_answer}")
        
        if user_answer and user_answer.upper() == correct_answer.upper():
            correct += 1
    
    score = (correct / total) * 100 if total > 0 else 0
    print(f"DEBUG - Score: {score}% ({correct}/{total})")
    
    return round(score, 2), correct, total

def generate_mock_exam(num_questions=50, duration=60):
    """Generate a mock exam with questions from all topics"""
    questions = Question.query.all()
    
    if not questions:
        return [], duration
    
    if len(questions) > num_questions:
        return random.sample(questions, num_questions), duration
    else:
        return questions, duration

def get_user_overall_score(user_id):
    """Get user's overall score using centralized calculator"""
    performance_data = get_user_performance_data(user_id, 365)  # Use full year for overall score
    return performance_data['overall_score']