from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, EmailField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField


# WTForm for creating a blog post
class Add_Post_Form(FlaskForm):
    title = StringField('Blog Post Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    # author_name = StringField('Your Name', validators=[DataRequired()])
    bg_img_url = StringField('Blog Image URL', validators=[DataRequired(), URL()])
    blog_content = CKEditorField('Blog Content', validators=[DataRequired()])
    submit = SubmitField('Submit Post')

class Register_Form(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(message="Invalid email. Email should be in format 'john@mail.com'.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 chars.")])
    name = StringField('Your Name', validators=[DataRequired()])    
    submit = SubmitField('Sign Me Up!')

class Login_Form(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(message="Invalid email. Email should be in format 'john@mail.com'.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message="Password must be at least 6 chars.")])    
    submit = SubmitField('Sign In')

class Comment_Form(FlaskForm):
    text = CKEditorField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Comment')
