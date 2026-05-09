from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField, HiddenField
from wtforms.validators import DataRequired

class QuizAnswerForm(FlaskForm):
    question_id = HiddenField('Question ID')
    answer = RadioField('Answer', 
                       choices=[('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ('D', 'Option D')],
                       validators=[DataRequired(message='Please select an answer')])
    question_num = HiddenField('Question Number')
    total_questions = HiddenField('Total Questions')
    time_taken = HiddenField('Time Taken', default=0)
    submit = SubmitField('Next Question')