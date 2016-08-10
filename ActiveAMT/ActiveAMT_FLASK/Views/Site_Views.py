from flask import render_template, request, redirect, session, url_for

from ActiveAMT.ActiveAMT_DB.HIT_DB import HITDbHandler
from ActiveAMT.ActiveAMT_FLASK import app, UserDbHandler, flask_dir

import time, os, json

hit_db = HITDbHandler()
user_db = UserDbHandler()
user_creds = {}


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                    Template Rendering Methods

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@app.route('/index', methods=['GET'])
@app.route('/', methods=['GET'])
def homepage():
    """
    Shows the ActiveAMT homepage.
    """
    if not verify_login(url_for('homepage'), False):
        return redirect(url_for('login'))

    return render_template('Site/homepage.html', user=session, css='homepage.css')


@app.route('/howTo', methods=['GET'])
def how_to():
    """
    Simply renders the how to template for the site
    """
    if not verify_login(url_for('how_to'), False):
        return redirect('login')

    return render_template('Site/howto.html', user=session, title="How To Use", css='howto.css')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                Admin Only Template Rendering

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@app.route('/manageUsers', methods=['GET'])
def manage_users():
    """
    Renders the template for user management, passing forward all users
    """
    if not verify_login(url_for('manage_users'), True):
        return redirect('login')

    return render_template('Site/manage_users.html', user=session, title='User Management', css='manage_users.css',
                           users=user_db.get_all_users())


@app.route('/manageHITs', methods=['GET'])
def manage_hits():
    """
    Renders the template for the HIT management page, passing forward all HITs
    """
    if not verify_login(url_for('manage_hits'), True):
        return redirect('login')

    hits = hit_db.get_all_hits()

    for hit in hits:
        if hit['completed']:
            hit['completed'] = 'True'
        else:
            hit['completed'] = 'False'

        if 'variables' in hit:  # Produces angular error within ng-init
            del hit['variables']

    return render_template('Site/manage_hits.html', user=session, title="HIT Management", css='manage_hits.css',
                           hits=hits)


@app.route('/shutdown', methods=['POST'])
def server_shutdown():
    """
    Provides a way to shut down the Flask Server from the web browser.
    """
    shutdown = False

    if 'YES' in str(request.form['shutdown']).upper():
        shutdown = True

    if shutdown:
        try:
            request.environ.get('werkzeug.server.shutdown')()
            return render_template('Site/shutdown.html', user=session)
        except EnvironmentError:
            return render_template('Site/shutdown_error.html')

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                        Login/Logout Methods

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


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

    """ Submitted the login form """
    if request.method == 'POST':
        user_creds['username'] = request.form['username']
        user_creds['password'] = request.form['password']
        temp_user = user_db.login(user_creds)

        """ Adding user to session is the actual 'logging in' """
        if temp_user['is_user_valid']:
            session['is_admin'] = temp_user['is_admin']
            session['username'] = temp_user['username']
            session['password'] = temp_user['password']

            """ If the user requested a page other than the login...
                redirect them to the requested page, unless it requires admin and they are not. """
            if 'requested_page' in session and (session['requested_page']['needs_admin'] and session['is_admin']):
                return redirect(session['requested_page']['url'])

            return redirect(url_for('homepage'))
        else:
            session['login_error'] = temp_user['login_error']

    return render_template('Site/login.html', user=session, title='ActiveAMT - Login', css='login.css')


@app.route('/logout', methods=['GET'])
def logout():
    """
    Logs user out.
    """
    session.clear()

    return redirect('/login')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                   Database Management Methods

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@app.route('/delUser', methods=['POST'])
def delete_user():
    """
    Route to delete a user from the USER database
    """
    if 'username' not in session:
        return redirect('/login')

    user_db.del_user(request.form['user'])
    return redirect('/manageUsers')


@app.route('/addUser', methods=['POST'])
def add_user():
    """
    Route to add a user to the USER database
    """
    if 'username' not in session:
        return redirect('/login')

    user_db.add_user(request.form['username'], request.form['password'], bool(request.form['is_admin']))
    return redirect('/manageUsers')


@app.route('/updateUser', methods=['POST'])
def update_user():
    """
    Route to update the attributes of a user in the USER database
    """
    if 'username' not in session:
        return redirect('/login')

    user_db.update_user(str(request.form['old_username']), str(request.form['username']), str(request.form['password']),
                        (request.form['is_admin'] == 'true'))

    return redirect('/manageUsers')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

                           Helper Methods

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


@app.route('/downloadTable', methods=['POST'])
def download_table():

    post_data = request.form['hit_ids']

    hit_ids = post_data.split(',')
    del hit_ids[-1]

    print("\nIn download table....")
    print("\tHIT IDs: {}".format(hit_ids))

    hits = []

    for hit_id in hit_ids:
        hits.append(hit_db.get_hit_by_id(hit_id))

    if not os.path.exists(flask_dir + 'static' '/UserSavedTables'):
        os.mkdir(flask_dir + 'static' '/UserSavedTables')

    fname = 'filtered_hits{}.txt'.format(time.time())
    filtered_hits = open('{}static/UserSavedTables/{}'.format(flask_dir, fname), 'w')
    filtered_hits.write(json.dumps(hits))
    filtered_hits.close()

    return 'static/UserSavedTables/{}'.format(fname)


def verify_login(requested_site, requires_admin):
    """
    Helper method to make sure the user is properly logged in.


    If the key 'username' does not exist in the current session, the user has not been logged in.
    Thus, add the url that they were trying to access and the access level of that url to the current session.

    If the key 'username' does exist in the current session, the user was logged in, return the what was happening.
    """

    is_logged_in = True

    if 'username' not in session:
        session['requested_page'] = {
            'url': requested_site,
            'needs_admin': requires_admin
        }
        is_logged_in = False

    return is_logged_in
