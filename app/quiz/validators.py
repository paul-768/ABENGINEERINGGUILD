def validate_quiz_parameters(topic_id, num_questions):
    """Validate quiz parameters"""
    if not topic_id or not isinstance(topic_id, int):
        return False, "Invalid topic ID"
    
    if not num_questions or not isinstance(num_questions, int) or num_questions < 1 or num_questions > 50:
        return False, "Number of questions must be between 1 and 50"
    
    return True, ""

def validate_answer(question_id, answer):
    """Validate answer format"""
    if not question_id or not isinstance(question_id, int):
        return False, "Invalid question ID"
    
    if not answer or answer.upper() not in ['A', 'B', 'C', 'D']:
        return False, "Answer must be A, B, C, or D"
    
    return True, ""