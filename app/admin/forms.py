from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, SubmitField, RadioField
from wtforms.validators import DataRequired, Length

class TopicForm(FlaskForm):
    name = StringField('Topic Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Add Topic')

class QuestionForm(FlaskForm):
    topic_id = SelectField('Topic', coerce=int, validators=[DataRequired()])
    question_text = TextAreaField('Question Text', validators=[DataRequired()])
    option_a = StringField('Option A', validators=[DataRequired()])
    option_b = StringField('Option B', validators=[DataRequired()])
    option_c = StringField('Option C', validators=[DataRequired()])
    option_d = StringField('Option D', validators=[DataRequired()])
    correct_answer = RadioField('Correct Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    explanation = TextAreaField('Explanation')
    submit = SubmitField('Save Question')

class PAESForm(FlaskForm):
    code = StringField('PAES Code', validators=[DataRequired(), Length(max=50)])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    submit = SubmitField('Add PAES Standard')

class AnnouncementForm(FlaskForm):
    title = StringField('Announcement Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    is_pinned = SelectField('Priority', choices=[('False', 'Normal'), ('True', 'Pinned (Shows at top)')])
    attachment = FileField('Attachment', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'], 
                    'Images (JPG, PNG, GIF, WEBP) or Documents (PDF, DOC, XLS, TXT) only!')
    ])
    images = FileField('Images (multiple)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    submit = SubmitField('Post Announcement')