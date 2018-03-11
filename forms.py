from flask_wtf import FlaskForm
from wtforms import TextField,TextAreaField,IntegerField,PasswordField,BooleanField,validators,SelectField,DateTimeField,DateField,FloatField
from datetime import datetime
from pytz import timezone
import pytz

days_between_attempts = [(j, j) for j in range(401)]
class UserLoginForm(FlaskForm):
    """Creates a form which will allow the user to log into the system."""

    username = TextField([validators.required(), validators.length(max=20)])
    password = PasswordField()

class UserRegisterForm(FlaskForm):
    username = TextField([validators.required(), validators.length(max=20)])
    email = TextField()
    password = PasswordField([validators.required(), validators.length(max=20)])
    confirm_password = PasswordField([validators.required(), validators.length(max=20)])
    first_name = TextField([validators.required(), validators.length(max=20)])
    last_name = TextField([validators.required(), validators.length(max=20)])
    roll_number = TextField([validators.required(), validators.length(max=20)])
    institute = TextField([validators.required(), validators.length(max=20)])
    department = TextField([validators.required(), validators.length(max=20)])
    position = TextField([validators.required(), validators.length(max=20)])
    timezone = SelectField(choices=[(tz, tz) for tz in pytz.common_timezones],default = pytz.utc)

class CourseForm(FlaskForm):

    name = TextField("name",[validators.required(), validators.length(max=128)])
    enrollment = SelectField("enrollment",choices = [('default','Enroll Request'), ('open','Open Enrollment')])
    active = BooleanField(default=True)
    code = TextField([validators.required(), validators.length(max=20)])
    instructions = TextAreaField([validators.required(), validators.length(max=500)])
    start_enroll_time = DateTimeField(default=datetime.now())
    end_enroll_time = DateTimeField(default=datetime(2199, 1, 1))


class QuizForm(FlaskForm):

    start_date_time = DateTimeField(default=datetime.now())
    end_date_time = DateTimeField(default=datetime(2199, 1, 1))
    duration = IntegerField(default = 20)
    active = BooleanField(default = True)
    description = TextField([validators.length(max=256)])
    pass_criteria = FloatField(default = 40)
    attempts_allowed = SelectField(choices = [('default','1'), ('2','2'), ('3','3'), ('4','4'), ('5','5'), ('inf','infinite')])
    time_between_attempts = SelectField(choices = days_between_attempts)
    instructions = TextField(default = None)
    view_answerpaper = BooleanField(default = False)
    allow_skip = BooleanField(default = True)
    is_trial = BooleanField(default = False)
    weightage = FloatField(default = 1.0)
    is_exercise = BooleanField(default = False)



