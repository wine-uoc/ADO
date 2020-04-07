"""Signup & login forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class SignupForm(FlaskForm):
    """User Signup Form."""
    name = StringField('Name',
                       validators=[DataRequired()])
    org = StringField('Organization Name',
                      validators=[DataRequired()])
    email = StringField('Email',
                        validators=[Length(min=6),
                                    Email(message='Enter a valid email.'),
                                    DataRequired()])
    password = PasswordField('Password',
                             validators=[DataRequired(),
                                         Length(min=4, message='Select a stronger password.')])
    confirm = PasswordField('Confirm Your Password',
                            validators=[DataRequired(),
                                        EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    """User Login Form."""
    email = StringField('Email', validators=[DataRequired(),
                                             Email(message='Enter a valid email.')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


class WifiForm(FlaskForm):
    """Set-Wifi Form."""
    ssid = StringField('SSID',
                       validators=[DataRequired()])
    password = PasswordField('Password',
                             validators=[DataRequired()])
    # NOTE: now this is an on-off button controlled with JS, no need to be in the form
    # active = PasswordField('Activate Wifi',
    #                       validators=[DataRequired()])
    submit = SubmitField('Set Wifi')

