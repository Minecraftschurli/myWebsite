from flask import Blueprint, redirect, url_for, session
from flask_login import login_user, logout_user

from .decorators import *
from .functions import *

auth = Blueprint('auth', __name__)


@auth.route('/login')
@check_ip
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    return render_with_nav('login')


@auth.route('/login', methods=['POST'])
@check_ip
def login_post():
    remember = True if 'remember' in request.form and request.form['remember'] else False

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not valid_login(request.form['username'], request.form['password']):
        flash({'text': 'Please check your login details and try again.', 'head': 'Error!'}, 'alert')
        return redirect(url_for('auth.login'))  # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(login_manager.user_callback(request.form['username']), remember=remember)
    try:
        next_page = session['next']
    except KeyError:
        next_page = None
    # is_safe_url should check if the url is safe for redirects.
    # See http://flask.pocoo.org/snippets/62/ for an example.
    if next_page is None or not is_safe_url(next_page):
        return redirect(url_for('main.index'))

    return redirect(next_page or url_for('main.index'))


@auth.route('/signup')
@check_ip
def signup():
    return render_with_nav('signup', code=None)


@auth.route('/signup', methods=['POST'])
@check_ip
def signup_post():
    code = None
    if not ('email' in request.form and request.form['email']):
        code = "No email!"
    elif not ('password' in request.form and 'password-repeat' in request.form and request.form['password'] ==
              request.form['password-repeat']):
        code = "Passwords do not match!"
    else:
        ret, c = add_user(request.form['firstname'], request.form['lastname'], request.form['username'],
                          request.form['password'], request.form['email'])
        if not ret:
            if not ('username' in request.form and c is 'username'):
                code = "A User with this Username already exists!"
            elif not (c is 'email'):
                code = "Only one Account per Email is allowed!"
        else:
            return redirect(url_for('auth.login'))
    flash({'head': 'Error!', 'text': code}, 'alert')
    return render_with_nav('signup')


@auth.route('/logout')
@check_ip
@login_required
def logout():
    # remove the username from the session if it's there
    logout_user()
    return redirect(url_for('main.index'))
