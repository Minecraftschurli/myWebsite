import json
from datetime import datetime

import requests
from flask import Blueprint, redirect, jsonify

from libs import admin, configuration
from . import adresslistenGenerator
from .decorators import *
from .functions import *

main = Blueprint('main', __name__)

routes = [""]
key = configuration['contact_key']


@main.route('/')
@check_ip
def index():
    return render_template("home.html", nav=get_nav(""))


@main.route('/adr_gen', methods=['POST', 'GET'])
@permission_required('school')
@check_ip
def adr_gen():
    ta = ["", ""]
    if request.method == 'POST':
        ip = ".".join((
            str(adresslistenGenerator.get_byte(request.form['firstByte'])),
            str(adresslistenGenerator.get_byte(request.form['secondByte'])),
            str(adresslistenGenerator.get_byte(request.form['thirdByte'])),
            str(adresslistenGenerator.get_byte(request.form['fourthByte']))
        ))
        server_names = str(request.form["sName"]).replace(" ", "").splitlines()
        client_names = str(request.form["cName"]).replace(" ", "").splitlines()
        html = adresslistenGenerator.create(server_names, client_names, ip, int(request.form['snm'])).to_html()
        rows = html.splitlines()

        for e in rows:
            rows[rows.index(e)] = len(e)

        ta[0] = len(rows)
        ta[1] = max(rows)
    else:
        html = None

    s = '<style>\nul{\nmargin-top: 0;\nlist-style-type: none;\n}\nh4{\nmargin-top: ' \
        '2px;\nmargin-bottom: 5px;\n}\n</style>\n'
    return render_with_nav("adr_gen", request=request, out=html, calc_needles=adresslistenGenerator.calc_needles, ta=ta,
                           style=s)


@main.route('/sx')
@check_ip
def sx():
    json_obj = json.loads(str(requests.get('https://api.cfwidget.com/minecraft/mc-mods/Superheroes-X')
                              .content.decode('UTF-8')))
    datetime_obj = datetime.strptime(json_obj['download']['uploaded_at']['date'], '%Y-%m-%d %H:%M:%S.%f')
    json_obj['download']['uploaded_at']['date'] = datetime_obj.strftime('%b %d, %Y')
    datetime_obj = datetime.strptime(json_obj['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    json_obj['created_at'] = datetime_obj.strftime('%b %d, %Y')
    return render_with_nav('sx', info=json_obj)


@main.route('/countdown')
@check_ip
def countdown():
    return render_with_nav('countdown')


@main.route('/contact', methods=['GET', 'POST'])
@main.route('/contact?<remove>')
@check_ip
def contact(remove=-1):
    messages = []
    if check_permission('all'):
        return admin.admin_contact(remove=remove)
    message = {'type': 'success', 'text': '', 'head': 'Success!'}
    form = None
    if request.method == 'POST':
        try:
            data = {
                'subject': request.form['subject'],
                'message': request.form['message']
            }
            if check_permission('any'):
                user = current_user.to_dict()
                user.pop('password_hash')
                user.pop('permissions')
                user.pop('username')
                data.update(user)
            else:
                data.update({
                    'first_name': request.form['firstname'],
                    'last_name': request.form['lastname'],
                    'email': request.form['email']
                })
            new_contact_request = Contact(**data)
            db.session.add(new_contact_request)
            db.session.commit()
            message['text'] = 'Successfully sent'
        except Exception:
            message['type'] = 'alert'
            message['head'] = 'Alert!'
            message['text'] = 'An error occurred'
            form = request.form

    if len(message['text']) > 0:
        messages.append(message)
    flash_messages(messages)
    return render_with_nav('contact', loggedin=check_permission('any'), form=form)


@main.route('/get_contact_msgs', methods=['POST'])
@check_ip
def get_contact_msgs():
    global key
    if request.method == 'POST':
        if request.form['key'] == key:
            return jsonify(Contact.query.all())
    abort(423)


@main.route('/webspace')
@permission_required('school')
@check_ip
def webspace():
    return redirect('https://projekte.tgm.ac.at/2dhit/gburkl/')


@main.route('/github')
@check_ip
def github():
    return redirect('https://github.com/Minecraftschurli')


@main.route('/twitch')
@check_ip
def twitch():
    return redirect('https://www.twitch.tv/minecraftschurli')


@main.route('/twitter')
@check_ip
def twitter():
    return redirect('https://twitter.com/schurlibub')


@main.route('/<name>')
@check_ip
def where(name):
    if name in routes:
        return render_with_nav(name)
    elif any(x in name for x in ['xml', 'php', 'security', 'robots']):
        blacklist_ip(request.remote_addr)
        abort(423)
    else:
        abort(404)
