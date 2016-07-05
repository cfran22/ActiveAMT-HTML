from flask import render_template, request, redirect, session
from ActiveAMT.ActiveAMT_FLASK import app, UserDbHandler
from ActiveAMT.ActiveAMT_DB import HITDbHandler
import json
import os

hit_info = {}

hit_db = HITDbHandler()
user_db = UserDbHandler()

user_creds = {}

app.secret_key = os.urandom(24)


@app.route('/')
@app.route('/index')
def homepage():
    """
    Shows the ActiveAMT homepage.
    """
    """ If the current session does not have a 'username' key, the session must not be logged in """
    if 'username' not in session:
        return redirect('/login')

    return render_template('Site/homepage.html', user=session, css='homepage.css')


@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Logs user in.
    """

    global user_creds

    session['login_error'] = {
        'is_error': False,
        'error_message': 'Username and password do not match!'
    }

    if request.method == 'POST':
        user_creds['username'] = request.form['username']
        user_creds['password'] = request.form['password']
        temp_user = user_db.login(user_creds)

        """ Adding user to session is the actual 'logging in' """
        if temp_user['is_user_valid']:
            session['is_admin'] = temp_user['is_admin'][0]
            session['username'] = temp_user['username']
            session['password'] = temp_user['password']

            return redirect('/')
        else:
            session['login_error'] = temp_user['login_error']

    return render_template('Site/login.html', user=session, title='ActiveAMT - Login', css='login.css')


@app.route('/logout')
def logout():
    """
    Logs user out.
    """
    session.clear()

    return redirect('/login')


@app.route('/howTo')
def how_to():
    """
    Simply renders the how to template for the site
    """
    """ If the current session does not have a 'username' key, the session must not be logged in """
    if 'username' not in session:
        return redirect('/login')

    return render_template('Site/howto.html', user=session, title="How To Use", css='howto.css')


@app.route('/manageUsers')
def manage_users():
    """
    Renders the template for user management, passing forward all users
    """
    """ If the current session does not have a 'username' key, the session must not be logged in """
    if 'username' not in session:
        return redirect('/login')

    return render_template('Site/manage_users.html', user=session, title='User Management', css='manage_users.css',
                           users=user_db.get_all_users())


@app.route('/text_hit.html')
def text_hit():
    """
    Shows the template for a HIT of type 'txt'.
    """
    get_url_params(request.args)

    if hit_info['hitId']:
        db_hit = hit_db.get_hit_by_id(hit_info['hitId'])
        hit_info['hit_quest'] = db_hit.question

    return render_template('HITS/text_hit.html', enabled=is_enabled(), hit_info=hit_info)


@app.route('/pict_hit.html')
def picture_hit():
    """
    Shows the template for a HIT of type 'img'.
    """
    get_url_params(request.args)

    if hit_info['hitId']:
        db_hit = hit_db.get_hit_by_id(hit_info['hitId'])
        if db_hit.question:
            hit_info['hit_quest'] = db_hit.question
        if db_hit.img_src:
            hit_info['img_src'] = db_hit.img_src

    return render_template('HITs/pict_hit.html', enabled=is_enabled(), hit_info=hit_info)


@app.route('/getAnswer')
def get_answer():
    """
    Collects and returns the input field whose name is 'answer'. Handled by js in helpers.js.
    """

    hit_info['answer'] = request.args.get('answer')

    hit_db.set_answer_for_hit(hit_info['hitId'], hit_info['answer'])

    print("\n\t**** HIT[{}]: {} answered '{}' ****".format(hit_info['hitId'], hit_info['workerId'], hit_info['answer']))

    if not hit_db.get_remaining_hits():
        return redirect('shutdown?pin=092396')

    return "Thank you for your input!"


@app.route('/shutdown', methods=['GET', 'POST'])
def server_shutdown():
    """
    Provides a way to shut down the Flask Server from the web browser.
    """
    shutdown = False
    pin = ""

    if request.method == 'POST':
        if 'YES' in str(request.form['shutdown']).upper():
            shutdown = True
    else:
        pin = request.args.get('pin')

    if pin == "092396" or shutdown:
        try:
            request.environ.get('werkzeug.server.shutdown')()
            return render_template('Site/shutdown.html', user=session)
        except:
            return render_template('Site/shutdown_error.html')
    else:
        return "Incorrect Shutdown Pin!"


def get_url_params(request_args):
    """
    Helper method to extract the parameters from the URL request.
    """
    hit_info['hitId'] = request_args.get('hitId')
    hit_info['assignmentId'] = request_args.get('assignmentId')
    hit_info['workerId'] = request_args.get('workerId')


def is_enabled():
    """
    Helper method to check if the HIT should be submittable
    """
    enabled = ""
    if hit_info['assignmentId'] == 'ASSIGNMENT_ID_NOT_AVAILABLE' or hit_info['assignmentId'] is None:
        enabled = "disabled"

    return enabled
