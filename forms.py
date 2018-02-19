from flask_wtf import Form
from wtforms import TextField,PasswordField

class UserLoginForm(Form):
    """Creates a form which will allow the user to log into the system."""

    username = TextField()
    password = PasswordField()

    def clean(self):
        super(UserLoginForm, self).clean()
        try:
            u_name, pwd = self.cleaned_data["username"],\
                          self.cleaned_data["password"]
            user = authenticate(username=u_name, password=pwd)
        except Exception:
            raise forms.ValidationError(
                "Username and/or Password is not entered"
            )
        if not user:
            raise forms.ValidationError("Invalid username/password")
        return user



