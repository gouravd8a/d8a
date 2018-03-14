from flask import Flask,request,render_template,redirect,url_for,flash
from forms import UserLoginForm,CourseForm,QuizForm,UserRegisterForm,QuestionFilterForm
from wtforms import DateTimeField
import sqlite3 as sql
from datetime import datetime
from textwrap import dedent

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['TEMPLATES_AUTO_RELOAD'] = True

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
    				if ismoderator(conn,uid):
    					return redirect(url_for('moderator_dashboard'))
    				else:
    					return redirect(url_for('quizlist_user'))

    form = UserLoginForm()
    return render_template('yaksh/login.html', form=form)


@app.route('/exam/register',methods = ['POST', 'GET'])
def user_register():
    if request.method == 'POST':
    	user = request.form['username']
    	email = request.form['email']
    	password = request.form['password']
    	fname = request.form['first_name']
    	lname = request.form['last_name']
    	rno = request.form['roll_number']
    	institute = request.form['institute']
    	department = request.form['department']
    	position = request.form['position']
    	tzone = request.form['timezone']
    	ctime = datetime.now()
    	conn = sql.connect('db.sqlite3')
    	conn.row_factory = sql.Row
    	new = conn.execute("insert into auth_user (password,last_login,is_superuser,first_name,last_name,email,is_staff,is_active,date_joined,username) values (?,?,0,?,?,?,0,1,?,?)",(password,ctime,fname,lname,email,ctime,user,))
    	conn.commit()
    	fin = conn.execute("select * from auth_user where username = ?",(user,))
    	for row in fin:
    		uid = row['id']
    	new2 = conn.execute("insert into yaksh_profile (roll_number,institute,department,position,timezone,user_id,is_email_verified) values (?,?,?,?,?,?,0)",(rno,institute,department,position,tzone,uid,))
    	conn.commit()
    	conn.close()
    	if new2 and new:
    		return render_template('yaksh/hello2.html')


    form= UserRegisterForm()
    return render_template('yaksh/register.html',form = form)

@app.route('/exam/quizzes')
def quizlist_user():

	flash('You were successfully logged in')
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	course = conn1.execute("select * from yaksh_course")
	return render_template('yaksh/quizzes_user.html',courses=course)

@app.route('/exam/manage')
def moderator_dashboard():

	flash('You were successfully logged in')
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	course = conn1.execute("select * from yaksh_course")
	return render_template('yaksh/moderator_dashboard.html',course=course,user="Teacher")


@app.route('/exam/course_modules/<cid>')
def course_module(cid):

	return render_template('yaksh/course_modules.html')

@app.route('/exam/manage/courses/all_quizzes/',methods = ['POST', 'GET'])
def show_all_quizzes():
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	quizzes = conn1.execute("select * from yaksh_quiz")
	return render_template('yaksh/courses.html',quizzes = quizzes,type = "quiz")





def ismoderator(conn,uid):
	cursor = conn.execute("select * from auth_user_groups where user_id = ?",(uid,))
	for row in cursor:
		gid = row["group_id"]
		cursor = conn.execute("select * from auth_group where id = ?",(gid,))
		for row in cursor:
			name = row["name"]
			if(name == "moderator"):
				return True
	return False


@app.route('/exam/manage/courses')
def course():
	return render_template('yaksh/courses.html')



@app.route('/exam/manage/add_course')
def add_course():
	form = CourseForm()
	return render_template("yaksh/add_course.html",form = form)

@app.route('/exam/manage/monitor')
def monitor():
	return render_template('yaksh/monitor.html')

@app.route('/exam/manage/add_lesson')
def add_lesson():
	return render_template('yaksh/add_lesson.html')


@app.route('/exam/manage/addquiz/')
def add_quiz():

	form = QuizForm()
	return render_template('yaksh/add_quiz.html',form = form)



@app.route('/exam/manage/designquestionpaper/<qid>/<qpid>/')
def design_questionpaper(qid,qpid):

	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	for record in records:
		qpaper = record
	point_options= []
	questions = []
	questions2 = []
	qu = []
	records2 = conn.execute("select distinct(points) as p from yaksh_question")
	for record2 in records2:
		point_options.append(record2['p'])
	filter_form = QuestionFilterForm()
	filter_form.marks.choices = point_options
	question = conn.execute("select * from yaksh_questionpaper_fixed_questions where questionpaper_id = ?",(qpid,))
	for q in question:
		quesno = q['question_id']
		question1 = conn.execute("select * from yaksh_question where id = ?",(quesno,))
		questions.append(question1)
	question2 = conn.execute("select * from yaksh_questionpaper_fixed_questions where questionpaper_id = ?",(qpid,))
	for q1 in question2:
		quesno2 = q1['question_id']
		qu.append(quesno2)
	return render_template('yaksh/design_questionpaper.html',qpaper=qpaper,filter_form=filter_form,questions=questions2,fixed_questions=questions)


@app.route('/exam/manage/addquiz/<qid>/')
def edit_quiz(qid):

	form = QuizForm()
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	records = conn.execute("select * from yaksh_quiz where id = ?",(qid,))
	for record in records:
		start_date_time = record['start_date_time']
		end_date_time = record['end_date_time']
		duration = record['duration']
		active = record['active']
		description = record['description']
		pass_criteria = record['pass_criteria']
		attempts_allowed = record['attempts_allowed']
		time_between_attempts = record['time_between_attempts']
		view_answerpaper = record['view_answerpaper']
		allow_skip = record['allow_skip']
		weightage = record['weightage']
	
	form.start_date_time = start_date_time
	form.end_date_time = end_date_time
	form.description.data = description
	form.duration.data = duration 
	form.active.data = active 
	form.pass_criteria.data = pass_criteria 
	form.attempts_allowed.data = attempts_allowed 
	form.time_between_attempts.data = time_between_attempts 
	form.view_answerpaper.data = view_answerpaper 
	form.allow_skip.data = allow_skip 
	form.weightage.data = weightage 

	return render_template('yaksh/add_quiz.html',form = form)

@app.template_filter('get_questionpaper')
def get_question_paper(quiz):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	qid = quiz['id']
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	return records

@app.template_filter('get_questionpaperstatus')
def get_question_paper_status(quiz):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	qid = quiz['id']
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	for record in records:
		if record:
			return True
		else:
			return False



@app.template_filter('course_details')
def get_course_details(course):
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	cid = course['id']
	qname = []
	ts = []
	ps = []
	fs = []
	quiz = get_quizzes(cid)	
	for q in quiz:
		for q1 in q:
			qname.append(q1['description'])
			ts.append(get_total_students(q1,cid))
			ps.append(get_passed_students(q1,cid))
			fs.append(get_failed_students(q1,cid))
	print(ps)
	print(fs)
	return [(qname,ts,ps,fs)]


def get_quizzes(cid):
	conn = sql.connect('db.sqlite3')
	flash('You were successfully logged in')
	conn.row_factory = sql.Row
	quizdetails = []
	records = conn.execute("select * from yaksh_course_learning_module where course_id = ?",(cid,))
	for record in records:
		records1 = conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?",(record['learningmodule_id'],))
		for record1 in records1:
			records2 = conn.execute("select * from yaksh_learningunit where id = ?",(record1['learningunit_id'],))
			for record2 in records2:
				records3 = conn.execute("select * from yaksh_quiz where id = ?",(record2['quiz_id'],))
				quizdetails.append(records3)
	return quizdetails


def get_total_students(quiz,cid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	tot1 = 0
	qid = quiz['id']
	#print(qid)
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	for record in records:
		tot = conn.execute("select count(*) as c from yaksh_answerpaper where question_paper_id = ? and course_id = ?",(record['id'],cid,))
		for t in tot:
			tot1 = tot1 + t['c']
	return tot1




def get_passed_students(quiz,cid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	tot1 = 0

	qid = quiz['id']
	#print(qid)
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	for record in records:
		tot = conn.execute("select * from yaksh_answerpaper where question_paper_id = ? and course_id = ? and passed = 'true'",(record['id'],cid,))
		for t in tot:
			#print(t)
			tot1 = tot1 + 1
	return tot1

def get_failed_students(quiz,cid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	tot1 = 0
	qid = quiz['id']
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	for record in records:
		tot = conn.execute("select * from yaksh_answerpaper where question_paper_id = ? and course_id = ? and passed = 'false'",(record['id'],cid,))
		for t in tot:
			#print(t)
			tot1 = tot1 + 1
	#print(tot1)
	return tot1



if __name__ == '__main__':
	app.run(debug=True)