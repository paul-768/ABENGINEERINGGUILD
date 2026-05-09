# app/community/forms.py - COMPLETE FIXED VERSION
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

class PostForm(FlaskForm):
    title = StringField('Title', validators=[Optional(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired(message="Content is required")])
    topic_id = SelectField('Topic', coerce=int, validators=[Optional()])
    post_type = SelectField('Post Type', choices=[
        ('discussion', 'Discussion'),
        ('question', 'Question')
    ], default='discussion')
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired(message="Comment cannot be empty")])
    submit = SubmitField('Post Comment')