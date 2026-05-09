from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    website = StringField('Website', validators=[Optional(), URL(), Length(max=200)])

class CoverPhotoForm(FlaskForm):
    cover_photo = StringField('Cover Photo')