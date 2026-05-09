# app/messages/forms.py
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, SelectField
from wtforms.validators import DataRequired, Optional, Length

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[DataRequired(), Length(max=2000)])

class NewConversationForm(FlaskForm):
    user_search = StringField('Search users', validators=[Optional()])
    selected_user = SelectField('Select user', choices=[], validators=[DataRequired()])

class CreateGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    is_private = SelectField('Privacy', choices=[('False', 'Public'), ('True', 'Private')])