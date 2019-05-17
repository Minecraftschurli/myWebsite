import json
import os
import sys
from os.path import getsize

from flask import Blueprint, redirect, Response, escape, url_for

from . import configuration
from .decorators import *
from .functions import *

admin = Blueprint('admin', __name__)

last_size = getsize(configuration['logfile'])


@admin.route('/admin/dashboard')
@roles_required('admin')
@check_ip
def admin_endpoint():
    users = User.query.all()
    users = [u for u in sorted(users, key=lambda x: x.username.lower())]
    return render_with_nav('admin/admin', users=users, roles=[r.name for r in Role.query.all()], config=configuration)


def _restart():
    os.execl(sys.executable, sys.executable, *sys.argv)


@admin.route('/admin/command/<command>?<param>', methods=['POST'])
@admin.route('/admin/command/<command>?', methods=['POST'])
@roles_required('admin')
@check_ip
def admin_commands(command='', param=''):
    messages = []

    def toggle_camera(_=None):
        configuration['camera']['status'] = (not configuration['camera']['status'])
        messages.append(
            {'type': 'success', 'text': 'Turned camera ' + ('on' if configuration['camera']['status'] else 'off') + '!',
             'head': 'Success!'})

    def toggle_detect(_=None):
        configuration['camera']['use_detect'] = (not configuration['camera']['use_detect'])
        messages.append({'type': 'success', 'text': 'Turned camera face detection ' + (
            'on' if configuration['camera']['use_detect'] else 'off') + '!', 'head': 'Success!'})

    def nothing(_=None):
        pass

    def _remove_user(user):
        db_manager = get_user_manager().db_manager
        if not db_manager.delete_object(db_manager.find_user_by_username(user)):
            messages.append({'type': 'success', 'text': 'Removed user!', 'head': 'Success!'})
            db_manager.commit()
        else:
            messages.append({'type': 'alert', 'text': 'Failed removing user!', 'head': 'Fail!'})

    def restart(_=None):
        from threading import Timer
        t = Timer(10.0, _restart)
        t.start()

    def add_user_role(_=None):
        db_manager = get_user_manager().db_manager
        db_manager.add_user_role(User.query.filter_by(username=request.form.get('username')).first(),
                                 request.form.get('role'))
        db_manager.commit()
        messages.append({'type': 'success', 'text': 'Added role to user!', 'head': 'Success!'})

    def remove_user_role(userrole):
        userrole = json.loads(str(userrole).replace('\'', '"'))
        db_manager = get_user_manager().db_manager
        role = Role.query.filter_by(name=userrole[1]).first()
        user = db_manager.find_user_by_username(userrole[0])
        if not user:
            messages.append({'type': 'alert', 'text': 'User not found!', 'head': 'Error!'})
            return
        if not role:
            messages.append({'type': 'alert', 'text': 'Role not found!', 'head': 'Error!'})
            return
        user_role = UserRoles.query.filter_by(user_id=user.id, role_id=role.id).first()
        db_manager.delete_object(user_role)
        db.session.commit()
        messages.append({'type': 'success', 'text': 'Removed role from user!', 'head': 'Success!'})

    def add_role(_=None):
        db.session.add(Role(name=request.form.get('role')))
        db.session.commit()
        messages.append({'type': 'success', 'text': 'Created role!', 'head': 'Success!'})

    def remove_role(role):
        db_manager = get_user_manager().db_manager
        if not db_manager.delete_object(Role.query.filter_by(name=role).first()):
            messages.append({'type': 'success', 'text': 'Removed role!', 'head': 'Success!'})
            db_manager.commit()
        else:
            messages.append({'type': 'alert', 'text': 'Failed removing role!', 'head': 'Fail!'})

    {
        "remove_user": _remove_user,
        "toggle_camera": toggle_camera,
        "toggle_detect": toggle_detect,
        "restart": restart,
        "add_user_role": add_user_role,
        "remove_role": remove_role,
        "add_role": add_role,
        "remove_user_role": remove_user_role
    }.get(command, nothing)(param)
    flash_messages(messages)
    return redirect(url_for('admin.admin_endpoint'))


@admin.route('/admin/console')
@roles_required('admin')
@check_ip
def console():
    global last_size, cur_size
    cur_size = getsize(configuration['logfile'])
    data = {'content': []}
    if cur_size != last_size:
        with open(configuration['logfile'], 'r') as f:
            f.seek(last_size if cur_size > last_size else 0)
            text = f.read()
            f.close()
            last_size = cur_size
            data['content'] = escape(text).splitlines(True)
            for i in range(len(data['content'])):
                if '/admin/console' in data['content'][i]:
                    data['content'].pop(i)

    return Response(json.dumps(data))


def admin_contact(remove):
    messages = []
    msgs = Contact.query.all()
    if len(msgs) >= int(remove) > 0:
        db.session.delete(Contact.query.get(int(remove)))
        db.session.commit()
        messages.append({'type': 'success', 'head': 'Success!', 'text': 'Deleted message!'})
        flash_messages(messages)
        return redirect(url_for('main.contact'))
    flash_messages(messages)
    return render_with_nav('admin/admin_contact', contact=msgs)
