from urllib.parse import urlparse, urljoin

from flask import request, render_template, flash
from flask_login import current_user

from . import nav, login_manager
from .databases import *


def blacklist_ip(ip_addr):
    new_bl_ip = IPBlacklist(ip=ip_addr)
    db.session.add(new_bl_ip)
    db.session.commit()


def _check_ip():
    result = IPBlacklist.query.filter_by(ip=request.remote_addr).first()
    if result:
        return False
    else:
        return True


def get_nav(name):
    name = '/' + name
    nav_out = list()
    for n, d, p, e in nav:
        if p == 'any' or (check_permission(p)):
            if type(d) is list:
                projects_out = list()
                for n1, d1, p1, e1 in d:
                    if p1 == 'any' or (check_permission(p1)):
                        projects_out.append((n1, d1, e1))
                nav_out.append((n, projects_out, False, False))
            else:
                nav_out.append((n, d, name == d, e))
    if current_user.is_authenticated:
        nav_out.append(('Logout', '/logout', False, False))
    else:
        nav_out.append(('Login', '/login', False, False))

    return nav_out


def render_with_nav(name, **kwargs):
    return render_template(name + ".html", nav=get_nav(name), **kwargs)


def check_permission(permission):
    return current_user.is_authenticated and current_user.has_permission(permission)


def valid_login(name, password):
    if valid_user(name):
        return login_manager.user_callback(name).authenticate(password)
    return False


def add_user(fname, lname, name, password, email, permissions=None):
    if permissions is None:
        permissions = list()

    if User.query.filter_by(email=email).first():
        return False, 'email'
    elif User.query.filter_by(username=name).first():
        return False, 'username'

    if email == (name + '@student.tgm.ac.at') and not ('school' in permissions):
        permissions.append('school')
    # noinspection PyArgumentList
    new_user = User(first_name=fname, last_name=lname, username=name,
                    password_hash=bcrypt.generate_password_hash(password).decode('utf-8'), email=email,
                    permissions=', '.join(permissions))
    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    return True, None


def remove_user(name):
    user = User.query.get(name)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False


def valid_user(user):
    return user is not None and user is not "" and User.query.get(user)


def is_safe_url(target):
    if 'console' in target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def flash_messages(messages):
    for m in messages:
        m_type = m['type']
        m.pop('type')
        flash(m, m_type)
