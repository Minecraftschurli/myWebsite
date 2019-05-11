import json
from os.path import getsize

from flask import Blueprint, redirect, url_for, Response, escape

from . import configuration
from .decorators import *
from .functions import *

admin = Blueprint('admin', __name__)


@admin.route('/admin')
@permission_required('all')
@check_ip
def admin_endpoint():
    users = User.query.all()
    users = [u for u in sorted(users, key=lambda x: x.username.lower())]
    return render_with_nav('admin/admin', users=users, config=configuration)


@admin.route('/admin/<command>', methods=['POST', 'GET'])
@admin.route('/admin/remove_user/<param>', methods=['POST', 'GET'])
@permission_required(permission='all')
@check_ip
def admin_commands(command='remove_user', param=''):
    messages = []

    def edit_user_permissions(_=None):
        user = User.query.get(request.form['username'])
        if 'username' in request.form and 'permissions' in request.form and user:
            user.permissions = ', '.join(str(request.form['permissions']).splitlines())
            db.session.commit()
            messages.append(
                {'type': 'success', 'text': 'Edited user permissions for user: ' + user.username, 'head': 'Success!'})

    def toggle_camera(_=None):
        configuration['camera']['status'] = (not configuration['camera']['status'])
        messages.append(
            {'type': 'success', 'text': 'Turned camera ' + ('on' if configuration['camera']['status'] else 'off') + '!',
             'head': 'Success!'})

    def toggle_detect(_=None):
        configuration['camera']['use_detect'] = (not configuration['camera']['use_detect'])
        messages.append({'type': 'success', 'text': 'Turned camera face detection ' + (
            'on' if configuration['camera']['use_detect'] else 'off') + '!', 'head': 'Success!'})

    # def reload_config(_=None):
    #     save_config()
    #     load_config()
    #     messages.append({'type': 'success', 'text': 'Reloaded config!', 'head': 'Success!'})

    def nothing(_=None):
        pass

    def _remove_user(user):
        if remove_user(user):
            messages.append({'type': 'success', 'text': 'removed user', 'head': 'Success!'})
        else:
            messages.append({'type': 'alert', 'text': 'removed user', 'head': 'Fail!'})

    {
        "edit_user_permissions": edit_user_permissions,
        "remove_user": _remove_user,
        "toggle_camera": toggle_camera,
        "toggle_detect": toggle_detect,
        # "reload_config": reload_config
    }.get(command, nothing)(param)
    for m in messages:
        m_type = m['type']
        m.pop('type')
        flash(m, m_type)
    return redirect(url_for('admin.admin_endpoint'))


@admin.route('/admin/console')
@permission_required('all')
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
