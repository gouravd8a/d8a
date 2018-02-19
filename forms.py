from flask_wtf import FlaskForm
from wtforms import TextField,PasswordField

class UserLoginForm(FlaskForm):
    """Creates a form which will allow the user to log into the system."""

    username = TextField()
    password = PasswordField()





