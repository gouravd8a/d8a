from flask import Flask,request,render_template
from forms import UserLoginForm
import sqlite3 as sql


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'


@app.route('/',methods = ['POST', 'GET'])
def user_login():
    """Take the credentials of the user and log the user in."""
    if request.method == 'POST':
   
    	user = request.form['username']
    	password = request.form['password']
    	
    	conn = sql.connect('db.sqlite3')
    	conn.row_factory = sql.Row

    	cursor = conn.execute("select * from auth_user")
   
    	for row in cursor:
    			uname = row["first_name"]
    			pword = row["last_name"]
    			uid = row["id"]
    			if uname == user and pword == password:
    				return render_template('yaksh/hello.html')

    form = UserLoginForm()
    return render_template('yaksh/login.html', form=form)


if __name__ == '__main__':
	app.run(debug=True)