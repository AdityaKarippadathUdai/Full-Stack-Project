from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User, Book

class RegisterForm(FlaskForm):
    name = StringField('Name',
                       validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', 
                        validators=[DataRequired(), Length(max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_name(self, name):
        user = User.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('That name is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class AddBookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    author = StringField('Author', validators=[DataRequired(), Length(max=100)])
    isbn = StringField('ISBN', validators=[DataRequired(), Length(max=20)])
    category = SelectField('Category', choices=[
        ('Technology', 'Technology'),
        ('Arts', 'Arts'),
        ('Literature', 'Literature'),
        ('Science', 'Science'),
        ('History', 'History')
    ], validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    image = FileField('Book Image', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Add Book')
    
    def validate_isbn(self, isbn):
        book = Book.query.filter_by(isbn=isbn.data).first()
        if book:
            raise ValidationError('A book with this ISBN already exists.')

class BorrowBookForm(FlaskForm):
    book_id = IntegerField('Book ID', validators=[DataRequired()])
    return_date = StringField('Return Date', validators=[DataRequired()])
