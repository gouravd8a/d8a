from flask import Flask,request,render_template,redirect,url_for,flash,send_file
from forms import UserLoginForm,CourseForm,QuizForm,UserRegisterForm,QuestionFilterForm
from wtforms import DateTimeField
import sqlite3 as sql
from datetime import datetime
from textwrap import dedent
import pytz
import time
from pytz import timezone

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

@app.route('/exam/quizzes/')
def quizlist_user():

	flash('You were successfully logged in')
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	course = conn1.execute("select * from yaksh_course")
	return render_template('yaksh/quizzes_user.html',courses=course,user="Student",title="All Courses")

@app.route('/exam/manage')
def moderator_dashboard():

	flash('You were successfully logged in')
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	course = conn1.execute("select * from yaksh_course")
	return render_template('yaksh/moderator_dashboard.html',course=course,user="Teacher")


@app.route('/exam/course_modules/<cid>')
def course_module(cid):
	lmod = []
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	course = conn1.execute("select * from yaksh_course where id =?",(cid,))
	for course1 in course:
		c = course1
	lmodule = conn1.execute("select * from yaksh_course_learning_module where course_id = ?",(cid,))
	for l in lmodule:
		lid = l['learningmodule_id']
		record = conn1.execute("select * from yaksh_learningmodule where id = ?",(lid,))
		lmod.append(record)
	#print(lmod)
	return render_template('yaksh/course_modules.html',course=c,learning_modules=lmod,user ="Student")


@app.route('/exam/manage/courses/all_quizzes/',methods = ['POST', 'GET'])
def show_all_quizzes():
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	quizzes = conn1.execute("select * from yaksh_quiz")
	return render_template('yaksh/courses.html',quizzes = quizzes,type = "quiz")

@app.route('/exam/quizzes/view_module/<mid>/<cid>')
def view_module(mid,cid,msg= "none"):
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	all_modules = []
	if msg=="none":
		msg =""
	module = conn1.execute("select * from yaksh_learningmodule where id =?",(mid,))
	for mod in module:
		learning_module = mod
	record = conn1.execute("select * from yaksh_course where id =?",(cid,))
	for cou in record:
		course = cou
	records = conn1.execute("select * from yaksh_course_learning_module where course_id = ?",(cid,))
	for r in records:
		ycm = r['learningmodule_id']
		record = conn1.execute("select * from yaksh_learningmodule where id = ?",(ycm,))
		for rec in record:
			all_modules.append(rec)


	record = conn1.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ? limit 1",(mid,))
	for rec in record:
		first_unit = rec['learningunit_id']
	return render_template('yaksh/show_video.html',msg = msg,learning_module = learning_module,state ="module",course=course,all_modules = all_modules,first_unit=first_unit)

def has_questions(qpid):
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	records = conn1.execute("select * from yaksh_questionpaper_fixed_questions where questionpaper_id = ?",(qpid,))
	for record in records:
		if record:
			return "true"
	return "false"


def show_question(question,last_attempt,cid,mid,qpid,quiz,previous_question = None):
	quiz_type = 'Exam'
	can_skip = False
	if previous_question:
		delay_time = time_left_on_question(last_attempt,previous_question)
	else:
		delay_time = time_left_on_question(last_attempt,question)
	if previous_question and quiz['is_exercise']:
		if delay_time <= 0 or previous_question in questions_answered(last_attempt):
			can_skip = True
		question = previous_question
	if not question:
		msg = 'Congratulations!  You have successfully completed the quiz.'
		return complete()

	if not quiz['active']:
		reason = 'The quiz has been deactivated!'
		return complete()

	if not quiz['is_exercise']:
		if paper.time_left() <= 0:
			reason = 'Your time is up!'
			return complete()
	else:
		quiz_type = 'Exercise'
	if question in questions_answered(last_attempt):
		notification = (  'You have already attempted this question successfully'
            if question['type'] == "code" else
            'You have already attempted this question')
	return "hi"
          

     
@app.route('/exam/start/<qpid>/<mid>/<cid>/<attempt_num>')
@app.route('/exam/start/<qpid>/<mid>/<cid>')
def start(qpid,mid,cid,attempt_num=None):
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	userid = 1
	status = has_questions(qpid)
	if status == "false":
		return view_module(mid = mid,cid = cid ,msg="Quiz does not have Questions, please contact your '\
            'instructor/administrator.")
	records = conn1.execute("select * from yaksh_questionpaper where id =?",(qpid,))
	for record in records:
		question_paper = record
		quizid = record['quiz_id']
	records = conn1.execute("select * from yaksh_quiz where id =?",(quizid,))
	for reco in records:
		quiz = reco
		status1= expired(quiz)
		if status1 == "yes":
			return view_module(mid = mid,cid = cid ,msg="Quiz has expired.")
	last_attempt=get_user_last_attempt(qpid,userid,cid)
	if last_attempt and is_attempt_inprogress(last_attempt):
		print("hi")
		return show_question(
            question =current_question(last_attempt), last_attempt=last_attempt,
            cid = cid,mid =mid, qpid =qpid,quiz=quiz,
            previous_question=current_question(last_attempt)
        )
	timezone = pytz.utc
	return render_template('yaksh/intro.html',question_paper = question_paper,quiz= quiz,timezone = timezone,user = "Student",qpid= qpid, mid =mid,cid =cid)


def get_user_last_attempt(qpid,userid,cid):
	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	records = conn1.execute("select * from yaksh_answerpaper where question_paper_id = ? and course_id = ? and user_id = ? order by attempt_number desc",(qpid,cid,userid,))
	for record in records:
		last_attempt = record
		return last_attempt

def is_attempt_inprogress(attempt):
    if attempt['status'] == 'inprogress':
        return time_left(attempt) > 0

def time_left(attempt):

    secs = get_total_seconds(attempt)
    apid = attempt['id']
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    records = conn1.execute("select * from yaksh_answerpaper where id = ?",(apid,))
    for record in records:
    	qpid = record['question_paper_id']
    	records2= conn1.execute("select * from yaksh_questionpaper where id = ?",(qpid,))
    	for record2 in records2:
    		quizid = record2['quiz_id']
    		records3= conn1.execute("select * from yaksh_quiz where id = ?",(quizid,))
    		for record3 in records3:
    			qduration = record3['duration']
				
    total = qduration*60.0
    remain = max(total - secs, 0)
    return int(remain)

def time_left_on_question(attempt,question):
    secs = get_total_seconds(attempt)
    total = question['min_time']*60.0
    remain = max(total - secs, 0)
    #print(remain)
    return int(remain)
def current_question(attempt):

    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    questions1 =[]
    questions2 = []
    flag =0
    records = conn1.execute("select * from yaksh_answerpaper_questions_unanswered where answerpaper_id = ?",(apid,))
    for record in records:
    	questions1.append(record['question_id'])
    	if record:
    		flat =1
    records2 = conn1.execute("select * from yaksh_answerpaper_questions where answerpaper_id = ?",(apid,))
    for record2 in records2:
    	questions2.append(record2['question_id'])
    if flag == 0:
    	cur_question = get_current_question(attempt,questions2)
    else:
    	cur_question = get_current_question(attempt,questions1)
    return cur_question

def questions_answered(attempt):

    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    questions1 =[]
    records2 = conn1.execute("select * from yaksh_answerpaper_questions_answered where answerpaper_id = ?",(apid,))
    for record2 in records2:
    	questions1.append(record2['question_id'])
    return questions1

def get_current_question(attempt,questions):

    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    #print("jo")
    ordered_question_ids = [int(q) for q in attempt['questions_order'].split(',')]

	
    for qid in ordered_question_ids:
        if qid in questions:
            records = conn1.execute("select * from yaksh_question where id = ?",(qid,))
            for record in records:
            	question = record
            	#print(record['summary'])
            	return question



def get_total_seconds(attempt):


	t = str(datetime.now())
	nowtime = t[0:t.find(".")]
	dt = datetime.strptime( attempt['end_time'],'%Y-%m-%d %H:%M:%S') - datetime.strptime(attempt['start_time'],'%Y-%m-%d %H:%M:%S')
	secs = dt.seconds + dt.days*24*3600
	return secs


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


@app.route('/data/<filename>')
def data(filename):
	file = filename
	return send_file('static/'+file, attachment_filename=file)

@app.route('/exam/manage/addquiz/')
def add_quiz():

	form = QuizForm()
	return render_template('yaksh/add_quiz.html',form = form)

@app.route('/exam/show_lesson/<lid>/<mid>/<cid>/')
def show_lesson(lid,mid,cid):

	conn1 = sql.connect('db.sqlite3')
	conn1.row_factory = sql.Row
	all_modules = []
	module = conn1.execute("select * from yaksh_learningmodule where id =?",(mid,))
	for mod in module:
		learning_module = mod
	record = conn1.execute("select * from yaksh_course where id =?",(cid,))
	for cou in record:
		course = cou
	records = conn1.execute("select * from yaksh_course_learning_module where course_id = ?",(cid,))
	for r in records:
		ycm = r['learningmodule_id']
		record = conn1.execute("select * from yaksh_learningmodule where id = ?",(ycm,))
		for rec in record:
			all_modules.append(rec)
	record = conn1.execute("select * from yaksh_lesson where id =?",(lid,))
	for r in record:
		lesson =r
	record = conn1.execute("select * from yaksh_learningunit where lesson_id =?",(lid,))
	for r in record:
		current_unit =r
	return render_template('yaksh/show_video.html',current_unit = current_unit,lesson =lesson,state = "lesson",course = course, all_modules= all_modules, learning_module = learning_module)


@app.route('/exam/next_unit/<cid>/<mid>/<uid>/1/')
def get_nextunit(cid,mid,uid):
	
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	records = conn.execute("select * from yaksh_learningunit where id = ?",(uid,))
	for rec in records:
		utype = rec['type']
		if utype == "lesson":
			lessid = rec['lesson_id']
			return redirect('/exam/show_lesson/{0}/{1}/{2}'.format(
            lessid, mid, cid))


@app.route('/exam/next_unit/<cid>/<mid>/<cuid>')
def get_next_unit(cid,mid,cuid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row	
	uid =[]
	currid = int(cuid)
	records= conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?",(mid,))
	for r in records:
		uid.append(r['learningunit_id'])
		
	for a in range(len(uid)):

		if uid[a] == currid:
			ind = a+1
			if ind == len(uid):
				ind = 0
			break
	next_unit_id = uid[ind]

	records = conn.execute("select * from yaksh_learningunit where id = ?",(next_unit_id,))
	for rec in records:
		utype = rec['type']
		if utype == "lesson":
			lessid = rec['lesson_id']
			return redirect('/exam/show_lesson/{0}/{1}/{2}'.format(
            lessid, mid, cid))
		elif utype == "quiz":
			quizid = rec['quiz_id']
			records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(quizid,))
			for r in records:
				qpid = r['id']
				return redirect('/exam/start/{0}/{1}/{2}'.format(
            qpid, mid, cid))
	return "Sorry the quiz is not ready"

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

@app.template_filter('get_creator_name')
def get_creator_name(course):
	name= []
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	cid = course['id']
	records = conn.execute("select * from yaksh_course where id = ?",(cid,))
	for record in records:
		crid = 3
	records = conn.execute("select * from auth_user where id = ?",(crid,))
	for record in records:
		name.append(record['first_name']+" "+record['last_name'])
	return name


@app.template_filter('get_questionpaper')
def get_question_paper(quiz):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	qid = quiz['id']
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	return records

@app.template_filter('get_question_paper')
def get_questionpaper(uid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	qpid = []
	record = conn.execute("select * from yaksh_learningunit where id = ?",(uid,))
	for r in record:
		qid = r['quiz_id']
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	for r in records:
		qpid.append(r['id'])
		return qpid




@app.template_filter('has_question_paper')
def has_questionpaper(uid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	stat = []
	record = conn.execute("select * from yaksh_learningunit where id = ?",(uid,))
	for r in record:
		qid = r['quiz_id']
	records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?",(qid,))
	for record in records:
		stat.append("true")
		return stat
	stat.append("false")
	return stat

@app.template_filter('is_expired')
def is_expired(quiz):
	stat = []
	t = str(datetime.now())
	nowtime = t[0:t.find(".")]
	if time.strptime(quiz['start_date_time'],'%Y-%m-%d %H:%M:%S') <= time.strptime(nowtime,'%Y-%m-%d %H:%M:%S') < time.strptime(quiz['end_date_time'],'%Y-%m-%d %H:%M:%S'):
		stat.append("no")
	else:
		stat.append("yes")
	return stat


def expired(quiz):
	stat = []
	t = str(datetime.now())
	nowtime = t[0:t.find(".")]

	if time.strptime(quiz['start_date_time'],'%Y-%m-%d %H:%M:%S') <= time.strptime(nowtime,'%Y-%m-%d %H:%M:%S') < time.strptime(quiz['end_date_time'],'%Y-%m-%d %H:%M:%S'):
		return "no"
	else:
		return "yes"

@app.template_filter('has_file')
def has_file(lid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	stat = []
	record = conn.execute("select * from yaksh_lessonfile where lesson_id = ?",(lid,))
	for r in record:
		stat.append("true")
		return stat
	stat.append("false")
	return stat


@app.template_filter('get_file_name')
def get_file_name(lid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	stat = []
	record = conn.execute("select * from yaksh_lessonfile where lesson_id = ?",(lid,))	
	for r in record:
		stat.append(r['file'])
	return stat

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

@app.template_filter('get_module_status')
def get_module_status(mid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	stat =[]
	tmod= 0
	cmod =0
	records = conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?",(mid,))
	for record in records:
		tmod=tmod+1
		lid = record['learningunit_id']
		records2 =conn.execute("select * from yaksh_coursestatus where current_unit_id = ?",(lid,))
		for record2 in records2:
			if record2:
				csid = record2['id']
				records3 = conn.execute("select * from yaksh_coursestatus_completed_units where learningunit_id = ? and coursestatus_id = ?",(lid,csid,))
				for record3 in records3:
					cmod=cmod+1

	if tmod == 0:
		status= "not attempted"
	elif tmod == cmod:
		staus =" completed"
	else:
		status = "inprogress"
	stat.append(status)
	return stat


@app.template_filter('get_unit_status')
def get_unit_status(lid):

	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	stat =[]
	tmod= 0
	cmod =0
	records2 =conn.execute("select * from yaksh_coursestatus where current_unit_id = ?",(lid,))
	for record2 in records2:
		tmod = tmod+1
		if record2:
			csid = record2['id']
			records3 = conn.execute("select * from yaksh_coursestatus_completed_units where learningunit_id = ? and coursestatus_id = ?",(lid,csid,))
			for record3 in records3:
				cmod=cmod+1

	if tmod == 0:
		status= "not attempted"
	elif tmod == cmod:
		status ="completed"
	else:
		status ="inprogress"

	
	stat.append(status)
	return stat

@app.template_filter('get_learning_units')
def get_learning_units(mid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	lunits = []
	records = conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?",(mid,))
	for record in records:

		lid = record['learningunit_id']
		records2 = conn.execute("select * from yaksh_learningunit where id = ?",(lid,))
		for record2 in records2:
			lunits.append(record2)


	return lunits


@app.template_filter('get_description')
def get_description(qid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	records = conn.execute("select * from yaksh_quiz where id = ?",(qid,))
	return records


@app.template_filter('is_exercise')
def is_exercise(qid):
	ex = []
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	records = conn.execute("select * from yaksh_quiz where id = ?",(qid,))
	for record in records:
		ex.append(record['is_exercise'])
	return ex


@app.template_filter('get_lesson')
def get_lesson(lid):
	conn = sql.connect('db.sqlite3')
	conn.row_factory = sql.Row
	records = conn.execute("select * from yaksh_lesson where id = ?",(lid,))
	return records


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