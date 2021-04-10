from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify, Response)
from werkzeug.utils import secure_filename
app = Flask(__name__)

import sys, os, random
import imghdr
import cs304dbi as dbi
import helper
import uploadHelper
import loginHelper


app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

app.config['TRAP_BAD_REQUEST_ERRORS'] = True

app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1*1024*1024 # 1 MB

from flask_cas import CAS

CAS(app)

app.config['CAS_SERVER'] = 'https://login.wellesley.edu:443'
app.config['CAS_LOGIN_ROUTE'] = '/module.php/casserver/cas.php/login'
app.config['CAS_LOGOUT_ROUTE'] = '/module.php/casserver/cas.php/logout'
app.config['CAS_VALIDATE_ROUTE'] = '/module.php/casserver/serviceValidate.php'
app.config['CAS_AFTER_LOGIN'] = 'logged_in'
# the following doesn't work :-(
app.config['CAS_AFTER_LOGOUT'] = 'after_logout'



@app.route('/logged_in/')
def logged_in():
    ''' route to log in and to insert new usernames into the database '''
    flash('successfully logged in!')
    conn = dbi.connect()
    username = session['CAS_USERNAME']
    attribs = session['CAS_ATTRIBUTES']
    name = attribs['cas:givenName'] + ' ' + attribs['cas:sn']
    if attribs['cas:isStudent'] == 'Y':
        loginHelper.checkAndInsertPerson(conn, username, name, 'student')
        session['role'] = 'student' 
    elif attribs['cas:isFaculty'] == 'Y':
        loginHelper.checkAndInsertPerson(conn, username, name, 'professor')
        session['role'] = 'professor'  
    elif attribs['cas:isStaff'] == 'Y':
        loginHelper.checkAndInsertPerson(conn, username, name, 'PLTC Admin')  
        session['role'] = 'PLTC admin' 
    return redirect( url_for('index') )


@app.route('/')
def index():
    ''' route to home page which displays an about description
    with a navigation bar'''
    if '_CAS_TOKEN' in session:
        token = session['_CAS_TOKEN']
    if 'CAS_ATTRIBUTES' in session:
        attribs = session['CAS_ATTRIBUTES']
    if 'CAS_USERNAME' in session:
        is_logged_in = True
        username = session['CAS_USERNAME']
    else:
        is_logged_in = False
        username = None
    return render_template('main.html',
                            title='Tutor Repository: Home',
                            username=username,
                            is_logged_in=is_logged_in)

@app.route('/after_logout/')
def after_logout():
    ''' route to log out '''
    flash('successfully logged out!')
    return redirect( url_for('index') )


@app.route('/search/', methods = ['GET'])
def search():
    ''' route to display the search form which includes dropdown menus with 
    semesters, departments and sections from database '''
    if 'CAS_USERNAME' in session:
        conn=dbi.connect()
        semesters = helper.getAllSemesters(conn)
        departments = helper.getAllDepartments(conn)
        sections = helper.getAllSections(conn)
        return render_template('search.html', semesters = semesters,
        departments = departments,sections = sections)
    else:
        flash('You are not logged in.')
        return redirect( url_for('index') )


@app.route('/check/', methods = ['GET'])
def check(): 
    ''' route to display the check SIs form which includes dropdown menus with 
    inputs for semesters and weeks'''
    if 'CAS_USERNAME' in session:
        if session['role'] == 'professor' or session['role'] == 'PLTC Admin' or session['role'] == 'student': 
            conn=dbi.connect()
            semesters = helper.getAllSemesters(conn)
            return render_template('check.html', semesters = semesters)
        else:
            flash('This page is only accessible to PLTC administrators or Wellesley College faculty.')
            return redirect( url_for('index') )
    else:
        flash('You are not logged in.')
        return redirect( url_for('index') )


@app.route('/searchResults/', methods = ['GET'])
def searchResults():
    ''' route to display the matching materials from the database for search 
    functionality, including class, week, file, topic, kind'''
    semester = request.args['semester']
    department = request.args['department']
    classNumber = request.args['class']
    section = request.args['section']
    topic = request.args['topic']
    conn=dbi.connect()
    semesters = helper.getAllSemesters(conn)
    departments = helper.getAllDepartments(conn)
    sections = helper.getAllSections(conn)
    matches = helper.searchForMatches(conn,semester,department,classNumber,section,topic)
    if classNumber.isdigit() == False and classNumber != "":
        flash("Please enter only the number from the class. Example: Enter '304' not CS304.")
    elif len(matches) == 0:
        flash("Your search did not match any results in the database.")
    return render_template('searchResults.html', matches = matches, 
    semesters = semesters,departments = departments,sections = sections, 
    semester = semester, department = department, classNum = classNumber, 
    section = section, topic = topic)


@app.route('/checkResults/', methods = ['GET'])
def checkResults(): 
    ''' route to display usernames and names two tables, one matching SI leaders 
    who have uploaded materials in given week in given semester from the database 
    and the other matching those who have not uploaded'''
    conn=dbi.connect()
    semester = request.args['semesterSI']
    week = request.args['weekSI']
    SIsYes,SIsNo = helper.checkGoodBadSIs(conn,semester,week)
    return render_template('checkResults.html',SIsYes = SIsYes,
    SIsNo = SIsNo,semester = semester,week = week)


@app.route('/upload/', methods=["GET", "POST"])
def upload():
    ''' route to display upload files form to input information about the 
    SI materials being uploaded '''
    conn=dbi.connect()
    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        if (session['role'] == 'professor' or session['role'] == 'PLTC Admin' 
        or loginHelper.checkIfSI(conn, username) != None): 
            if request.method == 'GET':
                conn=dbi.connect()
                classInfo = helper.getClassInfo(conn)
                semesters = helper.getAllSemesters(conn)
                return render_template('upload.html', classInfo = classInfo, 
                                        semesters = semesters)
            else:
                try:
                    conn=dbi.connect()
                    classInfo = helper.getClassInfo(conn)
                    semesters = helper.getAllSemesters(conn)
                    classID = request.form['class']
                    week = request.form['week']
                    topic = request.form['topic']
                    kind = request.form['kind']
                    f = request.files['SI_material']
                    user_filename = f.filename 
                    filename = secure_filename('{}'.format(user_filename)) 
                    if uploadHelper.allowed_file(filename):
                        pathname = os.path.join(app.config['UPLOADS'],filename)
                        f.save(pathname)
                        uploader_id = session['CAS_USERNAME']
                        uploadHelper.insertFilename(conn,filename,classID,week,topic,kind,uploader_id)
                        flash('Upload successful')
                        return render_template('upload.html', classInfo = classInfo, 
                                            semesters = semesters)
                    else:
                        flash('File type is not supported')
                        return render_template('upload.html', classInfo = classInfo, 
                                        semesters = semesters)
                except Exception as err:
                    conn=dbi.connect()
                    classInfo = helper.getClassInfo(conn)
                    semesters = helper.getAllSemesters(conn)
                    flash('Upload failed because {why}'.format(why=err))
                    return render_template('upload.html', classInfo = classInfo, 
                                        semesters = semesters)
        else:
            flash('This page is only accessible to PLTC administrators, faculty and SI leaders.')
            return redirect( url_for('index') )
    else:
        flash('You are not logged in.')
        return redirect( url_for('index') )


@app.route('/file/<mID>')
def get_file(mID):
    conn = dbi.connect()
    curs = dbi.dict_cursor(conn)
    numrows = curs.execute(
        '''select fileName from Materials where mID = %s''',
        [mID])
    if numrows == 0:
        flash('No file for {}'.format(mID))
        return redirect(url_for('index'))
    row = curs.fetchone()
    return send_from_directory(app.config['UPLOADS'],row['fileName'])


@app.route('/uploaded_files/', methods=["GET", "POST"])
def uploaded_files():
    conn=dbi.connect()
    if 'CAS_USERNAME' in session:
        username = session['CAS_USERNAME']
        if (session['role'] == 'professor' or session['role'] == 'PLTC Admin' 
        or loginHelper.checkIfSI(conn, username) != None): 
            if request.method == 'GET':
                conn=dbi.connect()
                uploader_id = session['CAS_USERNAME']
                files = uploadHelper.get_uploaded_files(conn, uploader_id)
                return render_template('uploaded_files.html', 
                        uploader_id = uploader_id, files = files)
            else:
                if request.form['delete'] == 'delete': 
                    conn=dbi.connect()
                    mID = request.form['mID']
                    filedict = uploadHelper.get_fileName(conn, mID)
                    filename = filedict['fileName']
                    uploadHelper.delete_file(conn, mID)
                    pathname = os.path.join(app.config['UPLOADS'],filename)
                    os.remove(pathname)
                    flash('File deleted succesfully.')
                    return redirect(url_for('uploaded_files'))
        else:
            flash('This page is only accessible to PLTC administrators, faculty and SI leaders.')
            return redirect( url_for('index') )
    else:
        flash('You are not logged in.')
        return redirect(url_for('index'))


@app.route('/insertSI/', methods = ['GET', 'POST'])
def insertSI(): 
    ''' route to display the form for PLTC admins to assign students
        as SI leaders to specific classes'''
    if 'CAS_USERNAME' in session:   
        if (session['role'] == 'professor' or session['role'] == 'PLTC Admin' 
        or session['role'] == 'student') :
            if request.method == 'GET':
                conn=dbi.connect()
                classInfo = helper.getClassInfo(conn)
                students = loginHelper.getAllNames(conn)
                return render_template('insertSI.html', 
                                        students = students, classInfo = classInfo)
            else:
                username = request.form['name']
                classID = request.form['class']
                conn=dbi.connect()
                loginHelper.checkAndInsertSILeader(conn, username, classID)
                return redirect( url_for('insertSI') )
        else:
            flash('This page is only accessible to PLTC administrators or Wellesley College faculty.')
            return redirect( url_for('index'))
    else:
        flash('You are not logged in.')
        return redirect( url_for('index') )


@app.before_first_request
def init_db():
    dbi.cache_cnf()
    dbi.use('tutorrep_db') 

application = app

if __name__ == '__main__':
    import sys, os

    if len(sys.argv) > 1:
        port=int(sys.argv[1])
        if not(1943 <= port <= 1952):
            print('For CAS, choose a port from 1943 to 1952')
            sys.exit()
    else:
        port=os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)
