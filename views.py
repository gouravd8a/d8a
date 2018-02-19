from flask import Flask,request,render_template
from forms import UserLoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'


@app.route('/')
def user_login():
    """Take the credentials of the user and log the user in."""
    form = UserLoginForm()

    return render_template('yaksh/login.html', form=form)


if __name__ == '__main__':
	app.run(debug=True)