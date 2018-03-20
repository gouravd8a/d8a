from flask import Flask, request, render_template, redirect, url_for, flash, send_file
from forms import UserLoginForm, CourseForm, QuizForm, UserRegisterForm, QuestionFilterForm
from wtforms import DateTimeField
import sqlite3 as sql
from datetime import datetime, timedelta
from textwrap import dedent
import pytz
import time
from pytz import timezone

app = Flask(__name__)

app.config['SECRET_KEY'] = 'hard to guess string'
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.route('/', methods=['POST', 'GET'])
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
                if ismoderator(conn, uid):
                    return redirect(url_for('moderator_dashboard'))
                else:
                    return redirect(url_for('quizlist_user'))

    form = UserLoginForm()
    return render_template('yaksh/login.html', form=form)


@app.route('/exam/register', methods=['POST', 'GET'])
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
        new = conn.execute(
            "insert into auth_user (password,last_login,is_superuser,first_name,last_name,email,is_staff,is_active,date_joined,username) values (?,?,0,?,?,?,0,1,?,?)",
            (password, ctime, fname, lname, email, ctime, user,))
        conn.commit()
        fin = conn.execute("select * from auth_user where username = ?", (user,))
        for row in fin:
            uid = row['id']
        new2 = conn.execute(
            "insert into yaksh_profile (roll_number,institute,department,position,timezone,user_id,is_email_verified) values (?,?,?,?,?,?,0)",
            (rno, institute, department, position, tzone, uid,))
        conn.commit()
        conn.close()
        if new2 and new:
            return render_template('yaksh/hello2.html')

    form = UserRegisterForm()
    return render_template('yaksh/register.html', form=form)


@app.route('/exam/quizzes/')
def quizlist_user():
    flash('You were successfully logged in')
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    course = conn1.execute("select * from yaksh_course")
    return render_template('yaksh/quizzes_user.html', courses=course, user="Student", title="All Courses")


@app.route('/exam/manage')
def moderator_dashboard():
    flash('You were successfully logged in')
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    course = conn1.execute("select * from yaksh_course")
    return render_template('yaksh/moderator_dashboard.html', course=course, user="Teacher")


@app.route('/exam/course_modules/<cid>')
def course_module(cid):
    lmod = []
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    course = conn1.execute("select * from yaksh_course where id =?", (cid,))
    for course1 in course:
        c = course1
    lmodule = conn1.execute("select * from yaksh_course_learning_module where course_id = ?", (cid,))
    for l in lmodule:
        lid = l['learningmodule_id']
        record = conn1.execute("select * from yaksh_learningmodule where id = ?", (lid,))
        lmod.append(record)
    # print(lmod)
    return render_template('yaksh/course_modules.html', course=c, learning_modules=lmod, user="Student")


@app.route('/exam/manage/courses/all_quizzes/', methods=['POST', 'GET'])
def show_all_quizzes():
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    quizzes = conn1.execute("select * from yaksh_quiz")
    return render_template('yaksh/courses.html', quizzes=quizzes, type="quiz")


@app.route('/exam/quizzes/view_module/<mid>/<cid>')
def view_module(mid, cid, msg="none"):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    all_modules = []
    print("jj")
    if msg == "none":
        msg = ""
    module = conn1.execute("select * from yaksh_learningmodule where id =?", (mid,))
    for mod in module:
        learning_module = mod
    record = conn1.execute("select * from yaksh_course where id =?", (cid,))
    for cou in record:
        course = cou
    records = conn1.execute("select * from yaksh_course_learning_module where course_id = ?", (cid,))
    for r in records:
        ycm = r['learningmodule_id']
        record = conn1.execute("select * from yaksh_learningmodule where id = ?", (ycm,))
        for rec in record:
            all_modules.append(rec)

    record = conn1.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ? limit 1",
                           (mid,))
    for rec in record:
        first_unit = rec['learningunit_id']
    return render_template('yaksh/show_video.html', msg=msg, learning_module=learning_module, state="module",
                           course=course, all_modules=all_modules, first_unit=first_unit)


def has_questions(qpid):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    records = conn1.execute("select * from yaksh_questionpaper_fixed_questions where questionpaper_id = ?", (qpid,))
    for record in records:
        if record:
            return "true"
    return "false"


def show_question(question, last_attempt, cid, mid, qpid, quiz, error_message = None,notification=None, previous_question=None):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    quiz_type = 'Exam'
    can_skip = False
    if previous_question:
        delay_time = time_left_on_question(last_attempt, previous_question)
    else:
        delay_time = time_left_on_question(last_attempt, question)
    if previous_question != None and quiz['is_exercise'] == "true":
        if delay_time <= 0 or previous_question in questions_answered(last_attempt):
            can_skip = True
        question = previous_question
    if not question:
        msg = 'Congratulations!  You have successfully completed the quiz.'
        return complete(atno= last_attempt['attempt_number'],cid = cid,mid =mid,quiz = quiz,qpid =qpid, reason = msg)

    if quiz['active'] == "false":
        reason = 'The quiz has been deactivated!'
        return complete(atno= last_attempt['attempt_number'],cid = cid,mid =mid,quiz = quiz,qpid =qpid, reason = reason)
    la =None
    t_left = time_left(last_attempt)
    print(last_attempt['id'])
    print("yell")
    if quiz['is_exercise'] == "false":
        if t_left <= 0:
            reason = 'Your time is up!'
            return complete(atno= last_attempt['attempt_number'],cid = cid,mid =mid,quiz = quiz,qpid =qpid, reason = reason)
    else:
        quiz_type = 'Exercise'
    if question['id'] in questions_answered(last_attempt):
        print("love")
        records = conn1.execute("select * from yaksh_answer where question_id = ? order by id desc limit 1", (question['id'],))
        for r in records:
            la = int(r['answer'])
        notification = ('You have already attempted this question successfully'
        if question['type'] == "code" else
        'You have already attempted this question')

    all_modules = []
    
    records = conn1.execute("select * from yaksh_course_learning_module where course_id = ?", (cid,))
    for r in records:
        ycm = r['learningmodule_id']
        record = conn1.execute("select * from yaksh_learningmodule where id = ?", (ycm,))
        for rec in record:
            all_modules.append(rec)
    has_unanswered = has_unanswered_questions(last_attempt)
    records = conn1.execute("select * from yaksh_course where id =?", (cid,))
    for rec in records:
        course = rec
    test_cases = get_test_cases(question)
    records = conn1.execute("select * from yaksh_learningmodule where id = ?", (mid,))
    for rec in records:
        module = rec
    if notification != None:
        return render_template('yaksh/question.html', paper=last_attempt, time_left=t_left, test_cases=test_cases,
                               question=question, quiz=quiz, notification=notification,
                               last_attempt=la, course=course, module=module, can_skip=can_skip,
                               delay_time=delay_time, quiz_type=quiz_type, all_modules=all_modules,
                               has_unanswered=has_unanswered)
    else:
        return render_template('yaksh/question.html', paper=last_attempt, time_left=t_left, test_cases=test_cases,
                               question=question, quiz=quiz, last_attempt=la, course=course,
                               module=module, can_skip=can_skip, delay_time=delay_time, quiz_type=quiz_type,
                               all_modules=all_modules, has_unanswered=has_unanswered)


@app.route('/exam/quit/<atno>/<mid>/<qpid>/<cid>/<quizid>',methods=['POST'])
def quit(atno,mid,qpid,cid,quizid):
    """Show the quit page when the user logs out."""
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_quiz where id = ?",(quizid,))
    for record in records:
        quiz = record
    records = conn.execute("select * from yaksh_answerpaper where attempt_number = ? and question_paper_id = ? and course_id = ? and user_id =1", (atno,qpid,cid,))
    for record in records:
        paper = record
    return render_template('yaksh/quit.html',quiz= quiz,course_id =cid,question_paper_id = qpid,module_id =mid,attempt_number = atno,paper= paper)


@app.route('/exam/complete/<atno>/<mid>/<qpid>/<cid>/<quizid>/',methods=['POST'])
def complete(atno, mid, qpid,cid,quizid,reason =None):

    """Show a page to inform user that the quiz has been compeleted."""
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    if qpid is None:
        message = reason or "An Unexpected Error occurred. Please contact your '\
            'instructor/administrator.'"
        context = {'message': message}
        return render_template('yaksh/complete.html',attempt_number =atno,course_id= cid,module_id = mid,question_paper_id= qpid, message =message)
    else:
        records = conn.execute("select * from yaksh_answerpaper where attempt_number = ? and question_paper_id = ? and course_id = ? and user_id =1", (atno,qpid,cid,))
        for record in records:
            paper = record
        records2 = conn.execute("select * from yaksh_course where id = ?", (cid,))
        for record2 in records2:
            course = record2
        records2 = conn.execute("select * from yaksh_learningmodule where id = ?", (mid,))
        for record2 in records2:
            module = record2
        records2 = conn.execute("select * from yaksh_learningunit where quiz_id = ?", (quizid,))
        for record2 in records2:
            learning_unit = record2
        update_status(paper,"completed")
        set_end_time(paper,datetime.now())
        message = reason or "Quiz has been submitted"
        return render_template('yaksh/complete.html',message=message,paper = paper,module_id =mid,course_id = cid,learning_unit = learning_unit)

@app.route('/exam/<qid>/skip/<atno>/<mid>/<qpid>/<cid>/',methods=['POST'])
def skip(qid, atno, mid, qpid, cid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_questionpaper where id = ?", (qpid,))
    for record in records:
        quizid = record['quiz_id']
        records2 = conn.execute("select * from yaksh_quiz where id = ?", (quizid,))
        for record2 in records2:
            quiz = record2
    records = conn.execute(
        "select * from yaksh_answerpaper where question_paper_id = ? and attempt_number = ? and course_id = ?",
        (qpid, atno, cid,))
    for record in records:
        apid = record['id']
        paper = record
    records = conn.execute("select * from yaksh_question where id = ?", (qid,))
    for record in records:
        cur_question = record
    if request.method == "POST":
        next_question =get_next_question(paper,cur_question['id'])
        return show_question(
                question=next_question, last_attempt=paper,
                cid=cid, mid=mid, qpid=qpid, quiz=quiz,
                previous_question=cur_question)




@app.route('/exam/<qid>/check/<atno>/<mid>/<qpid>/<cid>/', methods=['POST'])
def check(qid, atno, mid, qpid, cid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_questionpaper where id = ?", (qpid,))
    for record in records:
        quizid = record['quiz_id']
        records2 = conn.execute("select * from yaksh_quiz where id = ?", (quizid,))
        for record2 in records2:
            quiz = record2
    records = conn.execute(
        "select * from yaksh_answerpaper where question_paper_id = ? and attempt_number = ? and course_id = ?",
        (qpid, atno, cid,))
    for record in records:
        apid = record['id']
        paper = record
    records = conn.execute("select * from yaksh_question where id = ?", (qid,))
    for record in records:
        cur_question = record
    print(request.form)
    if request.method == "POST":

        if cur_question['type'] == 'mcq':
            print("h")
            user_answer = request.form.get('answer')
            print(user_answer)
        elif cur_question['type'] == 'integer':
            try:
                user_answer = int(request.form.get('answer'))
            except ValueError:
                msg = "Please enter an Integer Value"
                return show_question(
                    question=cur_question, last_attempt=paper, notification=msg,
                    cid=cid, mid=mid, qpid=qpid, quiz=quiz,
                    previous_question=cur_question)
        elif cur_question['type'] == 'float':
            try:
                user_answer = float(request.form.get('answer'))
            except ValueError:
                msg = "Please enter a Float Value"
                return show_question(
                    question=cur_question, last_attempt=paper, notification=msg,
                    cid=cid, mid=mid, qpid=qpid, quiz=quiz,
                    previous_question=cur_question)

        elif cur_question['type'] == "string":
            user_answer = str(request.form.get('answer'))
        elif cur_question['type'] == "mcc":
            user_answer = request.form.getlist('answer')
        else:
            user_answer = request.form.get('answer')
        if not user_answer:
            msg = "Please submit a valid answer."
            print("er")
            return show_question(
                question=cur_question, last_attempt=paper,
                cid=cid, mid=mid, qpid=qpid, quiz=quiz,notification = msg,
                previous_question=cur_question)
        if cur_question['id'] in questions_answered(paper):
            new_answer = get_latest_answer(paper, cur_question['id'])
            aid = new_answer['id']
            records = conn.execute("update yaksh_answer set answer =?,correct = 'false' where id = ?",
                                   (user_answer, aid,))
            conn.commit()
        else:
            records = conn.execute(
                "insert into yaksh_answer (answer,error,marks,correct,skipped,question_id) values (?,'',0.0,'false','false',?)",
                (user_answer, cur_question['id'],))
            conn.commit()
            answ = get_latest_answer1(cur_question['id'])
            aid = answ['id']
            records = conn.execute("insert into yaksh_answerpaper_answers (answerpaper_id,answer_id ) values(?,?)",
                                   (paper['id'], aid,))
            conn.commit()

        result = validate_answer(paper=paper, cur_question=cur_question, aid=aid, user_answer=user_answer)

        next_question, error_message, paper = update_paper(aid, result, paper)
        return show_question(
                question=next_question, last_attempt=paper,
                cid=cid, mid=mid, qpid=qpid, quiz=quiz,error_message = error_message,
                previous_question=cur_question)


    else:
        return show_question(
                question=cur_question, last_attempt=paper,
                cid=cid, mid=mid, qpid=qpid, quiz=quiz,
                previous_question=cur_question)


    
def update_paper(aid,result,paper):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_answer where id = ?",(aid,))
    for record in records:
        answer = record
    cur_question = answer['question_id']
    records = conn.execute("select * from yaksh_question where id =?",(cur_question,))
    for rec in records:
        question = rec
    if result.get('success') == True:
        marks = question['points']
        error_message = None
        correct = True
        print("qwer")
        error = result.get('error')
    else:
        marks = 0
        correct = False
        error_message=result.get('error')
        error = result.get('error')
    next_question = add_completed_question(paper,cur_question)
    if answer['marks'] != marks:
        if answer['marks'] == 0 and marks > 0:
            st = "increase"
        else:
            st = "decrease"
        records = conn.execute("update yaksh_answer set marks = ? ,correct =? ,error = ? where id =?",(marks,correct,error,aid,))
        conn.commit()
        update_marks(aid,paper,st,'inprogress')
        set_end_time(paper,datetime.now())
    return next_question,error_message,paper

def add_completed_question(paper,question):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    aids = []
    records = conn.execute("select * from yaksh_answerpaper_questions_answered where answerpaper_id = ?",(paper['id'],))
    for record in records:
        aids.append(record['question_id'])
    if question not in aids:
        records = conn.execute("insert into yaksh_answerpaper_questions_answered (answerpaper_id,question_id) values(?,?)",(paper['id'],question,))
        conn.commit()
        records = conn.execute("delete from yaksh_answerpaper_questions_unanswered where answerpaper_id = ? and question_id =?",(paper['id'],question,))
        conn.commit()

    return get_next_question(paper,question)


def get_next_question(paper,question):

    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    all_questions = [int(q_id) for q_id in paper['questions_order'].split(',')]
    if len(all_questions) == 0:
        return None
    try:
        index = all_questions.index(int(question))
        next_id = all_questions[index+1]
    except (ValueError, IndexError):
        next_id = all_questions[0]
    records = conn.execute("select * from yaksh_question where id = ?",(next_id,))
    for record in records:
        next_question = record
    return next_question

       


def set_end_time(paper,etime):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    sstime = str(etime)
    end_time = sstime[0:sstime.find(".")]
    end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
    records = conn.execute("update yaksh_answerpaper set end_time = ? where id = ?",(end_time,paper['id'],))
    conn.commit()


def update_marks(aid,paper,st, state = "completed"):
    update_marks_obtained(aid,paper,st)
    update_percent(paper)
    update_passed(paper)
    update_status(paper,state)


def update_marks_obtained(aid,paper,st):
    marks = 0
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    qpid = paper['question_paper_id']
    qid = []
    records = conn.execute("select * from yaksh_answer where id = ?",(aid,))
    for record in records:
        qsid = record['question_id']
    records = conn.execute("select * from yaksh_question where id = ?",(qsid,))
    for record in records:
        mark = record['points']
    if st == "increase":
        if paper['marks_obtained']:
            marks = paper['marks_obtained']+float(mark)
        else:
            marks= float(mark)
    else:
        marks = paper['marks_obtained'] - float(mark)
    records = conn.execute("update yaksh_answerpaper set marks_obtained = ? where id = ?",(marks,paper['id'],))
    conn.commit()

def update_percent(paper):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_answerpaper where id = ?",(paper['id'],))
    for record in records:
        paper= record
    records = conn.execute("select * from yaksh_questionpaper where id = ?",(paper['question_paper_id'],))
    for record in records:
        tot = record['total_marks']
    if paper['marks_obtained'] != "Null":
        per = (float(paper['marks_obtained'])/float(tot))*100
        percent = round(per,2)
    records = conn.execute("update yaksh_answerpaper set percent = ? where id = ?",(percent,paper['id'],))
    conn.commit()


def update_passed(paper):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_answerpaper where id = ?",(paper['id'],))
    for record in records:
        paper= record
    if paper['percent'] !="Null":
        records = conn.execute("select * from yaksh_questionpaper where id = ?",(paper['question_paper_id'],))
        for record in records:
            quizid = record['quiz_id']
        records = conn.execute("select * from yaksh_quiz where id = ?",(quizid,))
        for record in records:
            pass_criteria = record['pass_criteria']

    if paper['percent'] >= pass_criteria:
        passed = True
    else:
        passed = False
    records = conn.execute("update yaksh_answerpaper set passed = ? where id = ?",(passed,paper['id'],))
    conn.commit()


def update_status(paper,status):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_answerpaper where id = ?",(paper['id'],))
    for record in records:
        paper= record
    records = conn.execute("update yaksh_answerpaper set status = ? where id = ?",(status,paper['id'],))
    conn.commit()


def validate_answer(paper, cur_question, aid, user_answer):
    result = {'success': False, 'error': 'Incorrect answer', 'weight': 0.0}
    if user_answer is not None:
        if cur_question['type'] == 'mcq':
            expected_answer = get_test_case(question=cur_question, correct=True)
            if int(user_answer.strip()) == expected_answer-1:
                print("llo")
                print(int(user_answer.strip()))
                print(expected_answer-1)
                result['success'] = True
                result['error'] = 'Correct answer'
            elif cur_question['type'] == 'mcc':
                expected_answers = get_test_casemc(question=cur_question, correct=True)
                if set(user_answer) == set(expected_answers):
                    result['success'] = True
                    result['error'] = 'Correct answer'
            elif cur_question['type'] == 'integer':
                expected_answers = get_test_casein(question=cur_question)
                if user_answer in expected_answers:
                    result['success'] = True
                    result['error'] = 'Correct answer'
            elif cur_question['type'] == 'float':
                expected_answers = get_test_casefl(question=cur_question)
                if user_answer in expected_answers:
                    result['success'] = True
                    result['error'] = 'Correct answer'
    return result


def get_latest_answer(paper, question_id):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    rec = conn.execute("select * from yaksh_answerpaper_answers where answerpaper_id = ?", (paper['id'],))
    for r in rec:
        ansid = r['answer_id']
    records = conn.execute("select * from yaksh_answer where question_id = ? and id = ?", (question_id, ansid,))
    for record in records:
        answer = record
    return answer


def get_latest_answer1(question_id):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_answer where question_id = ? order by id desc", (question_id,))
    for record in records:
        answer = record
    return answer


@app.route('/exam/start/<qpid>/<mid>/<cid>/<attempt_num>/', methods=['POST', 'GET'])
@app.route('/exam/start/<qpid>/<mid>/<cid>/')
def start(qpid, mid, cid, attempt_num=None):
    #print("hi")
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    userid = 1
    status = has_questions(qpid)
    if status == "false":
        return view_module(mid=mid, cid=cid, msg="Quiz does not have Questions, please contact your '\
            'instructor/administrator.")
    records = conn1.execute("select * from yaksh_questionpaper where id =?", (qpid,))
    for record in records:
        question_paper = record
        quizid = record['quiz_id']
    records = conn1.execute("select * from yaksh_quiz where id =?", (quizid,))
    for reco in records:
        quiz = reco
        status1 = expired(quiz)
        if status1 == "yes":
            return view_module(mid=mid, cid=cid, msg="Quiz has expired.")
    last_attempt = get_user_last_attempt(qpid, userid)
    if last_attempt and is_attempt_inprogress(last_attempt):
        return show_question(
            question=current_question(last_attempt), last_attempt=last_attempt,
            cid=cid, mid=mid, qpid=qpid, quiz=quiz,
            previous_question=current_question(last_attempt))
    if can_attempt_now(qpid, cid, userid, quiz) == "false":
        msg = "You cannot attempt {0} quiz more than {1} time(s)".format(
            quiz['description'], quiz['attempts_allowed'])
        return view_module(mid=mid, cid=cid, msg=msg)

    if not last_attempt:
        attempt_number = 1

    else:
        attempt_number = last_attempt['attempt_number'] + 1

    if attempt_num == None and quiz['is_exercise'] == "false":
        attempt_num = attempt_number

        timezone = pytz.utc
        return render_template('yaksh/intro.html', attempt_number=attempt_num, question_paper=question_paper, quiz=quiz,
                               timezone=timezone, user="Student", qpid=qpid, mid=mid, cid=cid)
    else:

        userip = request.remote_addr
        new_paper = make_answerpaper(cid, userip, attempt_number, question_paper, user="Student", quiz=quiz)
        if new_paper['status'] == "inprogress":
            return show_question(question=current_question(new_paper),
                                 last_attempt=new_paper, cid=cid,
                                 mid=mid, qpid=qpid, quiz=quiz, previous_question=None
                                 )


def make_answerpaper(cid, userip, attempt_number, question_paper, user, quiz):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    stime = datetime.now()
    sstime = str(stime)
    start_time = sstime[0:sstime.find(".")]
    start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    end_time = start_time + timedelta(minutes=quiz['duration'])
    et = str(end_time)
    etime = et[0:et.find(".")]
    end_time = datetime.strptime(etime, '%Y-%m-%d %H:%M:%S')
    qpid = question_paper['id']
    questions = get_ordered_questions(question_paper)
    question_ids = [str(que['id']) for que in questions]
    questions_order = ",".join(question_ids)
    status = "inprogress"
    print(questions_order)
    records = conn.execute(
        "insert into yaksh_answerpaper (attempt_number,start_time,comments,end_time,user_ip,status,question_paper_id,user_id,questions_order,course_id) values (?,?,?,?,?,?,?,1,?,?)",
        (attempt_number, start_time, "hello", end_time, userip, status, qpid, questions_order, cid))
    conn.commit()
    records = conn.execute(
        "select * from yaksh_answerpaper where attempt_number = ? and question_paper_id = ? and user_id = 1",
        (attempt_number, qpid,))
    for record in records:
        apid = record['id']
        ans_paper = record
    for que in questions:
        quid = que['id']
        records = conn.execute(
            "insert into yaksh_answerpaper_questions_unanswered (answerpaper_id,question_id) values (?,?)",
            (apid, quid))
        conn.commit()

    return ans_paper


def get_ordered_questions(question_paper):
    ques = []
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    if (question_paper['fixed_question_order']):
        que_order = question_paper['fixed_question_order'].split(',')
        for que_id in que_order:
            records = conn.execute("select * from yaksh_question where id = ?", (que_id,))
            for record in records:
                ques.append(record)
    return ques


def is_attempt_allowed(qpid, userid, quiz):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select count(*) as c from yaksh_answerpaper where question_paper_id = ? and user_id = ?",
                           (qpid, userid,))
    for record in records:
        cou = record['c']
    if quiz['attempts_allowed'] == cou:
        return "false"
    else:
        return "true"


def can_attempt_now(qpid, cid, userid, quiz):
    if is_attempt_allowed(qpid, userid, quiz) == "true":
        last_attempt = get_user_last_attempt(qpid, userid)
        if last_attempt:
            time_lag = (datetime.now() - datetime.strptime(last_attempt['start_time'], '%Y-%m-%d %H:%M:%S')).days
            return time_lag >= quiz['time_between_attempts']
        else:
            return "true"
    else:
        return "false"


def get_user_last_attempt(qpid, userid):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    records = conn1.execute(
        "select * from yaksh_answerpaper where question_paper_id = ? and user_id = ? order by attempt_number desc",
        (qpid, userid,))
    for record in records:
        last_attempt = record
        return last_attempt


def is_attempt_inprogress(attempt):
    print("yoyo")
    if attempt['status'] == 'inprogress':
        return time_left(attempt) > 0


def get_test_cases(question):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    qid = question['id']
    tc = []
    records = conn1.execute("select * from yaksh_testcase where question_id = ?", (qid,))
    for record in records:
        tid = record['id']
        records2 = conn1.execute("select * from yaksh_mcqtestcase where testcase_ptr_id = ?", (tid,))
        for record2 in records2:
            tc.append(record2)

    return tc


def get_test_case(question, correct):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    qid = question['id']
    records = conn1.execute("select * from yaksh_testcase where question_id = ?", (qid,))
    for record in records:
        tid = record['id']
        records2 = conn1.execute("select * from yaksh_mcqtestcase where testcase_ptr_id = ? and correct = ?",
                                 (tid, correct,))
        for record2 in records2:
            tid = record2['testcase_ptr_id']

    return tid


def get_test_casein(question):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    qid = question['id']
    tc = []
    records = conn1.execute("select * from yaksh_testcase where question_id = ?", (qid,))
    for record in records:
        tid = record['id']
        records2 = conn1.execute("select * from yaksh_integertestcase where testcase_ptr_id = ?", (tid,))
        for record2 in records2:
            tc.append(record2['correct'])
    return tc


def get_test_casefl(question):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    qid = question['id']
    tc = []
    records = conn1.execute("select * from yaksh_testcase where question_id = ?", (qid,))
    for record in records:
        tid = record['id']
        records2 = conn1.execute("select * from yaksh_mcqtestcase where testcase_ptr_id = ?", (tid,))
        for record2 in records2:
            tc.append(record2['correct'])

    return tc


def get_test_casemc(question, correct):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    qid = question['id']
    tc = []
    records = conn1.execute("select * from yaksh_testcase where question_id = ?", (qid,))
    for record in records:
        tid = record['id']
        records2 = conn1.execute("select * from yaksh_mcqtestcase where testcase_ptr_id = ? and correct = ?",
                                 (tid, correct,))
        for record2 in records2:
            tc.append(record2['testcase_ptr_id'])

    return tc


def time_left(attempt):
    secs = get_total_seconds(attempt)
    apid = attempt['id']
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    records = conn1.execute("select * from yaksh_answerpaper where id = ?", (apid,))
    for record in records:
        qpid = record['question_paper_id']
        records2 = conn1.execute("select * from yaksh_questionpaper where id = ?", (qpid,))
        for record2 in records2:
            quizid = record2['quiz_id']
            records3 = conn1.execute("select * from yaksh_quiz where id = ?", (quizid,))
            for record3 in records3:
                qduration = record3['duration']

    total = qduration * 60.0
    remain = max(total - secs, 0)
    return int(remain)


def get_total_seconds(attempt):
    t = str(datetime.now())
    nowtime = t[0:t.find(".")]
    print(nowtime)
    dt = datetime.strptime(nowtime, '%Y-%m-%d %H:%M:%S') - datetime.strptime(attempt['start_time'], '%Y-%m-%d %H:%M:%S')
    secs = dt.seconds + dt.days * 24 * 3600
    # print(secs)
    return secs


def time_left_on_question(attempt, question):
    secs = get_total_seconds(attempt)
    total = question['min_time'] * 60.0
    remain = max(total - secs, 0)
    # print(remain)
    return int(remain)


def current_question(attempt):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    questions1 = []
    questions2 = []
    flag = 0
    records = conn1.execute("select * from yaksh_answerpaper_questions_unanswered where answerpaper_id = ?", (apid,))
    for record in records:
        questions1.append(record['question_id'])
        if record:
            flag = 1
    records2 = conn1.execute("select * from yaksh_answerpaper_questions where answerpaper_id = ?", (apid,))
    for record2 in records2:
        questions2.append(record2['question_id'])
    if flag == 0:
        cur_question = get_current_question(attempt, questions2)
    else:
        cur_question = get_current_question(attempt, questions1)
    return cur_question


def questions_answered(attempt):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    questions1 = []
    records2 = conn1.execute("select * from yaksh_answerpaper_questions_answered where answerpaper_id = ?", (apid,))
    for record2 in records2:
        questions1.append(record2['question_id'])
    return questions1


def has_unanswered_questions(attempt):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    records2 = conn1.execute("select * from yaksh_answerpaper_questions_unanswered where answerpaper_id = ?", (apid,))
    for record2 in records2:
        return "true"
    return "false"


def get_current_question(attempt, questions):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    # print("jo")
    ordered_question_ids = [int(q) for q in attempt['questions_order'].split(',')]

    for qid in ordered_question_ids:
        if qid in questions:
            records = conn1.execute("select * from yaksh_question where id = ?", (qid,))
            for record in records:
                question = record
                # print(record['summary'])
                return question


def ismoderator(conn, uid):
    cursor = conn.execute("select * from auth_user_groups where user_id = ?", (uid,))
    for row in cursor:
        gid = row["group_id"]
        cursor = conn.execute("select * from auth_group where id = ?", (gid,))
        for row in cursor:
            name = row["name"]
            if (name == "moderator"):
                return True
    return False


@app.route('/exam/manage/courses')
def course():
    return render_template('yaksh/courses.html')


@app.route('/exam/manage/add_course')
def add_course():
    form = CourseForm()
    return render_template("yaksh/add_course.html", form=form)


@app.route('/exam/manage/monitor')
def monitor():
    return render_template('yaksh/monitor.html')


@app.route('/exam/manage/add_lesson')
def add_lesson():
    return render_template('yaksh/add_lesson.html')


@app.route('/data/<filename>')
def data(filename):
    file = filename
    return send_file('static/' + file, attachment_filename=file)


@app.route('/exam/manage/addquiz/')
def add_quiz():
    form = QuizForm()
    return render_template('yaksh/add_quiz.html', form=form)


@app.route('/exam/show_lesson/<lid>/<mid>/<cid>/')
def show_lesson(lid, mid, cid):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    all_modules = []
    module = conn1.execute("select * from yaksh_learningmodule where id =?", (mid,))
    for mod in module:
        learning_module = mod
    record = conn1.execute("select * from yaksh_course where id =?", (cid,))
    for cou in record:
        course = cou
    records = conn1.execute("select * from yaksh_course_learning_module where course_id = ?", (cid,))
    for r in records:
        ycm = r['learningmodule_id']
        record = conn1.execute("select * from yaksh_learningmodule where id = ?", (ycm,))
        for rec in record:
            all_modules.append(rec)
    record = conn1.execute("select * from yaksh_lesson where id =?", (lid,))
    for r in record:
        lesson = r
    record = conn1.execute("select * from yaksh_learningunit where lesson_id =?", (lid,))
    for r in record:
        current_unit = r
    return render_template('yaksh/show_video.html', current_unit=current_unit, lesson=lesson, state="lesson",
                           course=course, all_modules=all_modules, learning_module=learning_module)


@app.route('/exam/next_unit/<cid>/<mid>/<uid>/1/')
def get_nextunit(cid, mid, uid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_learningunit where id = ?", (uid,))
    for rec in records:
        utype = rec['type']
        if utype == "lesson":
            lessid = rec['lesson_id']
            return redirect('/exam/show_lesson/{0}/{1}/{2}'.format(
                lessid, mid, cid))
        if utype == "quiz":
            quizid = rec['quiz_id']
            records2 = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (quizid,))
            for r in records2:
                qpid = r['id']
                return redirect('/exam/start/{0}/{1}/{2}'.format(
                    qpid, mid, cid))
    print("qwww")
    return "Sorry the quiz is not ready"



@app.route('/exam/next_unit/<cid>/<mid>/<cuid>')
def get_next_unit(cid, mid, cuid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    uid = []
    currid = int(cuid)
    records = conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?", (mid,))
    for r in records:
        uid.append(r['learningunit_id'])

    for a in range(len(uid)):

        if uid[a] == currid:
            ind = a + 1
            if ind == len(uid):
                ind = 0
            break
    next_unit_id = uid[ind]

    records = conn.execute("select * from yaksh_learningunit where id = ?", (next_unit_id,))
    for rec in records:
        utype = rec['type']
        if utype == "lesson":
            lessid = rec['lesson_id']
            return redirect('/exam/show_lesson/{0}/{1}/{2}'.format(
                lessid, mid, cid))
        elif utype == "quiz":
            quizid = rec['quiz_id']
            records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (quizid,))
            for r in records:
                qpid = r['id']
                return redirect('/exam/start/{0}/{1}/{2}'.format(
                    qpid, mid, cid))
    return "Sorry the quiz is not ready"


@app.route('/exam/manage/designquestionpaper/<qid>/<qpid>/')
def design_questionpaper(qid, qpid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
    for record in records:
        qpaper = record
    point_options = []
    questions = []
    questions2 = []
    qu = []
    records2 = conn.execute("select distinct(points) as p from yaksh_question")
    for record2 in records2:
        point_options.append(record2['p'])
    filter_form = QuestionFilterForm()
    filter_form.marks.choices = point_options
    question = conn.execute("select * from yaksh_questionpaper_fixed_questions where questionpaper_id = ?", (qpid,))
    for q in question:
        quesno = q['question_id']
        question1 = conn.execute("select * from yaksh_question where id = ?", (quesno,))
        questions.append(question1)
    question2 = conn.execute("select * from yaksh_questionpaper_fixed_questions where questionpaper_id = ?", (qpid,))
    for q1 in question2:
        quesno2 = q1['question_id']
        qu.append(quesno2)
    return render_template('yaksh/design_questionpaper.html', qpaper=qpaper, filter_form=filter_form,
                           questions=questions2, fixed_questions=questions)


@app.route('/exam/manage/addquiz/<qid>/')
def edit_quiz(qid):
    form = QuizForm()
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_quiz where id = ?", (qid,))
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

    return render_template('yaksh/add_quiz.html', form=form)


@app.template_filter('get_creator_name')
def get_creator_name(course):
    name = []
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    cid = course['id']
    records = conn.execute("select * from yaksh_course where id = ?", (cid,))
    for record in records:
        crid = 3
    records = conn.execute("select * from auth_user where id = ?", (crid,))
    for record in records:
        name.append(record['first_name'] + " " + record['last_name'])
    return name


@app.template_filter('get_questions_unanswered')
def get_questions_unanswered(attempt, qid):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    questions1 = []
    sta = []
    records2 = conn1.execute("select * from yaksh_answerpaper_questions_unanswered where answerpaper_id = ?", (apid,))
    for record2 in records2:
        questions1.append(record2['question_id'])

    if qid['id'] in questions1:
        sta.append("true")
        return sta
    else:
        sta.append("false")
        return sta


@app.template_filter('get_questions_answered')
def get_questions_answered(attempt, qid):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    questions1 = []
    sta = []
    records2 = conn1.execute("select * from yaksh_answerpaper_questions_answered where answerpaper_id = ?", (apid,))
    for record2 in records2:
        questions1.append(record2['question_id'])

    if qid['id'] in questions1:
        sta.append("true")
        return sta
    else:
        sta.append("false")
        return sta

@app.template_filter('allquestions')
def allquestions(attempt):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    questions = []
    records = conn1.execute("select * from yaksh_questionpaper_fixed_questions where questionpaper_id = ?", (attempt['question_paper_id'],))
    for record in records:
        qid = record['question_id']
        records2 = conn1.execute("select * from yaksh_question where id = ?", (qid,))
        for record2 in records2:
            questions.append(record2)
    return questions
        


@app.template_filter('get_questionpaper')
def get_question_paper(quiz):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    qid = quiz['id']
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
    return records


@app.template_filter('get_question_paper')
def get_questionpaper(uid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    qpid = []
    record = conn.execute("select * from yaksh_learningunit where id = ?", (uid,))
    for r in record:
        qid = r['quiz_id']
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
    for r in records:
        qpid.append(r['id'])
        return qpid


@app.template_filter('has_question_paper')
def has_questionpaper(uid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    stat = []
    record = conn.execute("select * from yaksh_learningunit where id = ?", (uid,))
    for r in record:
        qid = r['quiz_id']
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
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
    if time.strptime(quiz['start_date_time'], '%Y-%m-%d %H:%M:%S') <= time.strptime(nowtime,
                                                                                    '%Y-%m-%d %H:%M:%S') < time.strptime(
            quiz['end_date_time'], '%Y-%m-%d %H:%M:%S'):
        stat.append("no")
    else:
        stat.append("yes")
    return stat


def expired(quiz):
    stat = []
    t = str(datetime.now())
    nowtime = t[0:t.find(".")]

    if time.strptime(quiz['start_date_time'], '%Y-%m-%d %H:%M:%S') <= time.strptime(nowtime,
                                                                                    '%Y-%m-%d %H:%M:%S') < time.strptime(
            quiz['end_date_time'], '%Y-%m-%d %H:%M:%S'):
        return "no"
    else:
        return "yes"


@app.template_filter('has_file')
def has_file(lid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    stat = []
    record = conn.execute("select * from yaksh_lessonfile where lesson_id = ?", (lid,))
    for r in record:
        stat.append("true")
        return stat
    stat.append("false")
    return stat


@app.template_filter('get_all_ordered_questions')
def get_all_ordered_questions(paper):
    ordered_question_ids = [int(q) for q in paper['questions_order'].split(',')]
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    questions = []
    for qid in ordered_question_ids:
        records = conn.execute("select * from yaksh_question where id =?", (qid,))
        for record in records:
            questions.append(record)
    return questions


@app.template_filter('get_file_name')
def get_file_name(lid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    stat = []
    record = conn.execute("select * from yaksh_lessonfile where lesson_id = ?", (lid,))
    for r in record:
        stat.append(r['file'])
    return stat


@app.template_filter('questions_left')
def questions_left(attempt):
    conn1 = sql.connect('db.sqlite3')
    conn1.row_factory = sql.Row
    apid = attempt['id']
    no = []
    questions1 = []
    records2 = conn1.execute("select * from yaksh_answerpaper_questions_unanswered where answerpaper_id = ?", (apid,))
    for record2 in records2:
        questions1.append(record2['question_id'])
    no.append(len(questions1))
    return no


@app.template_filter('get_questionpaperstatus')
def get_question_paper_status(quiz):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    qid = quiz['id']
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
    for record in records:
        if record:
            return True
        else:
            return False


@app.template_filter('get_module_status')
def get_module_status(mid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    stat = []
    tmod = 0
    cmod = 0
    records = conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?", (mid,))
    for record in records:
        tmod = tmod + 1
        lid = record['learningunit_id']
        records2 = conn.execute("select * from yaksh_coursestatus where current_unit_id = ?", (lid,))
        for record2 in records2:
            if record2:
                csid = record2['id']
                records3 = conn.execute(
                    "select * from yaksh_coursestatus_completed_units where learningunit_id = ? and coursestatus_id = ?",
                    (lid, csid,))
                for record3 in records3:
                    cmod = cmod + 1

    if tmod == 0:
        status = "not attempted"
    elif tmod == cmod:
        status = " completed"
    else:
        status = "inprogress"
    stat.append(status)
    return stat


@app.template_filter('get_unit_status')
def get_unit_status(lid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    stat = []
    tmod = 0
    cmod = 0
    records2 = conn.execute("select * from yaksh_coursestatus where current_unit_id = ?", (lid,))
    for record2 in records2:
        tmod = tmod + 1
        if record2:
            csid = record2['id']
            records3 = conn.execute(
                "select * from yaksh_coursestatus_completed_units where learningunit_id = ? and coursestatus_id = ?",
                (lid, csid,))
            for record3 in records3:
                cmod = cmod + 1

    if tmod == 0:
        status = "not attempted"
    elif tmod == cmod:
        status = "completed"
    else:
        status = "inprogress"

    stat.append(status)
    return stat


@app.template_filter('get_learning_units')
def get_learning_units(mid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    lunits = []
    records = conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?", (mid,))
    for record in records:

        lid = record['learningunit_id']
        records2 = conn.execute("select * from yaksh_learningunit where id = ?", (lid,))
        for record2 in records2:
            lunits.append(record2)

    return lunits


@app.template_filter('get_description')
def get_description(qid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_quiz where id = ?", (qid,))
    return records


@app.template_filter('is_exercise')
def is_exercise(qid):
    ex = []
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_quiz where id = ?", (qid,))
    for record in records:
        ex.append(record['is_exercise'])
    return ex


@app.template_filter('get_lesson')
def get_lesson(lid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    records = conn.execute("select * from yaksh_lesson where id = ?", (lid,))
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
            ts.append(get_total_students(q1, cid))
            ps.append(get_passed_students(q1, cid))
            fs.append(get_failed_students(q1, cid))
    return [(qname, ts, ps, fs)]


def get_quizzes(cid):
    conn = sql.connect('db.sqlite3')
    flash('You were successfully logged in')
    conn.row_factory = sql.Row
    quizdetails = []
    records = conn.execute("select * from yaksh_course_learning_module where course_id = ?", (cid,))
    for record in records:
        records1 = conn.execute("select * from yaksh_learningmodule_learning_unit where learningmodule_id = ?",
                                (record['learningmodule_id'],))
        for record1 in records1:
            records2 = conn.execute("select * from yaksh_learningunit where id = ?", (record1['learningunit_id'],))
            for record2 in records2:
                records3 = conn.execute("select * from yaksh_quiz where id = ?", (record2['quiz_id'],))
                quizdetails.append(records3)
    return quizdetails


def get_total_students(quiz, cid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    tot1 = 0
    qid = quiz['id']
    # print(qid)
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
    for record in records:
        tot = conn.execute("select count(*) as c from yaksh_answerpaper where question_paper_id = ? and course_id = ?",
                           (record['id'], cid,))
        for t in tot:
            tot1 = tot1 + t['c']
    return tot1


def get_passed_students(quiz, cid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    tot1 = 0

    qid = quiz['id']
    # print(qid)
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
    for record in records:
        tot = conn.execute(
            "select * from yaksh_answerpaper where question_paper_id = ? and course_id = ? and passed = 'true'",
            (record['id'], cid,))
        for t in tot:
            # print(t)
            tot1 = tot1 + 1
    return tot1


def get_failed_students(quiz, cid):
    conn = sql.connect('db.sqlite3')
    conn.row_factory = sql.Row
    tot1 = 0
    qid = quiz['id']
    records = conn.execute("select * from yaksh_questionpaper where quiz_id = ?", (qid,))
    for record in records:
        tot = conn.execute(
            "select * from yaksh_answerpaper where question_paper_id = ? and course_id = ? and passed = 'false'",
            (record['id'], cid,))
        for t in tot:
            # print(t)
            tot1 = tot1 + 1
    # print(tot1)
    return tot1


if __name__ == '__main__':
    app.run(debug=True)