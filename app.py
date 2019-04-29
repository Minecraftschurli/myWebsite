import json
import platform
import time
from datetime import datetime
from os.path import getsize

import requests
import screenutils as screen
from flask import *
from flask_bcrypt import Bcrypt

import libs.adresslistenGenerator as aG
from libs.ShootItData import ShootItData
from libs.camera import VideoCamera
from libs.user import User

configs = dict()


def load_config():
    with open('./conf.json', 'r') as conf:
        json_obj = json.load(conf)
        for k, v in json_obj.items():
            configs[k] = v


def save_config():
    with open('./conf.json', 'w') as conf:
        json.dump(configs, conf, indent=4)


load_config()

if platform.system() is not 'Windows':
    import meinheld

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.secret_key = bytes(configs['secret_key'], 'UTF-8')

shootit_data = ShootItData()

nav = [("Home", "/", "any", False),
       ("Projects", [
           ("Superheroes X", "/sx", "any", False),
           ("ShootIt", "/games/shootit", "any", False),
           ("ITBoy", "/games/itboy", "any", False),
           ("Adresslistengenerator", "/nwtk", "nwtk", False)
       ], "any", False),
       ("Links", [
           ("GitHub <i class='fab fa-github' style='font-size: 120%;'></i>", "/github", "any", True),
           ("Twitch <i class='fab fa-twitch' style='font-size: 120%;color: purple'></i>", "/twitch", "any", True),
           ("Twitter <i class='fab fa-twitter' style='font-size: 120%;color: #55ACEE'></i>", "/twitter", "any", True),
           ("TGM - Projektserver", "/webspace", "nwtk", True)
       ], "any", False),
       ("Contact", "/contact", "any", False),
       # ("Cam", "/cam", "camera", False),
       ("Admin", "/admin", "all", False)]

routes = [""]
cams = [0]

users = {}

testfile = './testfile.txt'


class TestScreen(object):
    def __init__(self):
        self.logs = TestScreen.gen()

    def enable_logs(self, filename=None):
        self.logs = TestScreen.gen()

    def disable_logs(self, remove_logfile=False):
        self.logs = None

    def send_commands(self, *commands):
        for command in commands:
            f = open(testfile, 'a')
            f.write('<web-console> ' + command + '\n')
            f.close()
            from threading import Thread
            thread = Thread(target=self.execute(command))
            thread.start()

    @staticmethod
    def execute(command):
        def exe():
            if str(command).lower() == 'test':
                lines = [str(i) + '\n' for i in ['Test Start', *range(10), 'Test End']]
                for line in lines:
                    f = open(testfile, 'a')
                    f.write(line)
                    f.close()
                    time.sleep(1)
            elif str(command).lower() in ['hello', 'hi']:
                time.sleep(3)
                f = open(testfile, 'a')
                f.write('Hello Admin\n')
                f.close()

        return exe

    @staticmethod
    def gen():
        last_size = getsize(testfile)
        while True:
            cur_size = getsize(testfile)
            if cur_size != last_size:
                with open(testfile, 'r') as f:
                    f.seek(last_size if cur_size > last_size else 0)
                    text = f.read()
                    f.close()
                    last_size = cur_size
                    yield text


if platform.system() is not 'Windows':
    current_screen = screen.list_screens()[0]
else:
    current_screen = TestScreen()


@app.route('/')
def index():
    return render_template("home.html", nav=get_nav(""))


@app.route('/admin')
@app.route('/admin/<command>', methods=['POST', 'GET'])
@app.route('/admin/remove_user/<param>', methods=['POST', 'GET'])
def admin(command='', param=''):
    messages = []

    def reload_user(_=None):
        save_users()
        load_users()
        messages.append({'type': 'success', 'text': 'reloaded users', 'head': 'Success!'})

    def edit_user_permissions(_=None):
        if 'username' in request.form and 'permissions' in request.form and request.form['username'] in users:
            users[request.form['username']].permissions = str(request.form['permissions']).split(', ')
            reload_user()
        messages.append({'type': 'success', 'text': 'edit user permissions', 'head': 'Success!'})

    def _remove_user(user):
        remove_user(user)
        reload_user()
        messages.append({'type': 'success', 'text': 'removed user', 'head': 'Success!'})

    def toggle_camera(_=None):
        configs['camera'] = (not configs['camera'])
        messages.append(
            {'type': 'success', 'text': 'turned camera ' + ('on' if configs['camera'] else 'off'), 'head': 'Success!'})

    def reload_config(_=None):
        save_config()
        load_config()
        messages.append({'type': 'success', 'text': 'reloaded config', 'head': 'Success!'})

    def nothing(_=None):
        pass

    if check_permission('all'):
        {
            "reload_user": reload_user,
            "edit_user_permissions": edit_user_permissions,
            "remove_user": _remove_user,
            "toggle_camera": toggle_camera,
            "reload_config": reload_config
        }.get(command, nothing)(param)
        return render_with_nav("admin", users=users.items(), config=configs, messages=messages)
    else:
        abort(423)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and valid_login(request.form['username'], request.form['password']):
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    else:
        return render_with_nav('login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    code = None
    if request.method == 'POST':
        if not ('email' in request.form and request.form['email']):
            code = "No email"
        elif not ('username' in request.form and request.form['username'] not in users):
            code = "User already exists"
        elif not ('password' in request.form and 'password-repeat' in request.form and request.form['password'] ==
                  request.form['password-repeat']):
            code = "Passwords do not match"
        else:
            add_user(request.form['firstname'], request.form['lastname'], request.form['username'],
                     request.form['password'], request.form['email'])
            save_users()
            load_users()
            return redirect(url_for('login'))
    return render_with_nav('register', code=code)


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route('/nwtk', methods=['POST', 'GET'])
def nwtk():
    if not check_permission('nwtk'):
        return redirect(url_for('login'))
    ta = ["", ""]
    if request.method == 'POST':
        ip = ".".join((
            str(aG.get_byte(request.form['firstByte'])),
            str(aG.get_byte(request.form['secondByte'])),
            str(aG.get_byte(request.form['thirdByte'])),
            str(aG.get_byte(request.form['fourthByte']))
        ))
        server_names = str(request.form["sName"]).replace(" ", "").splitlines()
        client_names = str(request.form["cName"]).replace(" ", "").splitlines()
        html = aG.create(server_names, client_names, ip, int(request.form['snm'])).to_html()
        app.logger.debug(html)
        rows = html.splitlines()

        for e in rows:
            rows[rows.index(e)] = len(e)

        ta[0] = len(rows)
        ta[1] = max(rows)
    else:
        html = None

    s = '<style>\nul{\nmargin-top: 0;\nlist-style-type: none;\n}\nh4{\nmargin-top: ' \
        '2px;\nmargin-bottom: 5px;\n}\n</style>\n'
    return render_with_nav("nwtk", request=request, out=html, calc_needles=aG.calc_needles, ta=ta, style=s)


@app.route('/sx')
def sx():
    json_obj = json.loads(str(requests.get('https://api.cfwidget.com/minecraft/mc-mods/Superheroes-X')
                              .content.decode('UTF-8')))
    datetime_obj = datetime.strptime(json_obj['download']['uploaded_at']['date'], '%Y-%m-%d %H:%M:%S.%f')
    json_obj['download']['uploaded_at']['date'] = datetime_obj.strftime('%b %d, %Y')
    datetime_obj = datetime.strptime(json_obj['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    json_obj['created_at'] = datetime_obj.strftime('%b %d, %Y')
    return render_with_nav('sx', info=json_obj)


@app.route('/games/shootit')
def shootit():
    shootit_data.refresh()
    if 'username' in session and valid_user(session['username']):
        data = shootit_data.get_data_for_user(session['username'])
        if data is None:
            shootit_data.create_and_get_user(session['username'], assoc=session['username'])
    return render_with_nav('game', game_name='ShootIt', game_src='../static/games/shootit/game.html')


@app.route('/games/itboy')
def itboy():
    return render_with_nav('game', game_name='ITBoy', game_src='../static/games/itboy/ITBoy.html',
                           game_settings=""
                                         "aside {width: 100%;position: relative;overflow: hidden;max-width: 100%;}"
                                         "main {overflow-y: scroll;width: 1027px;min-width: 1027px;position: relative;padding: 10px}"
                                         "#fullscreen {display: none;}"
                                         ".iframe-cont iframe {border: inset 2px;height: 99.5%;width: 99%;resize: none;}"
                                         ".iframe-cont {resize: none;padding-bottom: 4px;}")


@app.route('/static/games/shootit/GetOrCreateUserProfile?<opt>', methods=["POST"])
@app.route('/static/games/shootit/GetOrCreateUserProfile', methods=["POST"])
def get_or_create_user_profile(opt=""):
    shootit_data.refresh()
    c = False
    new = False
    if 'username' in session and valid_user(session['username']):
        data = shootit_data.get_data_for_user(session['username'])
        if data is None:
            data = shootit_data.create_and_get_user(request.form['username'], assoc=session['username'])
        c = True
    elif opt != "nocreate" and 'username' in request.form:
        if shootit_data.user_exists(request.form['username']):
            data = shootit_data.get_anonymus_user(request.form['username'])
        else:
            data = shootit_data.create_and_get_user(request.form['username'])
            new = True
        c = True
    else:
        data = {}
    shootit_data.refresh()
    return jsonify(**data, check=c, new=new)


@app.route('/static/games/shootit/UpdateUserProfile', methods=["POST"])
def update_user_profile():
    shootit_data.update(request.form['user'], request.form['difficulty'], request.form['score'])
    return Response()


@app.route('/static/games/shootit/highscore', methods=["POST"])
def get_highscores():
    highscores = shootit_data.get_highscores(request.form['difficulty'])
    out = "<tr><th>Nr.</th><th width='80px'>Name</th><th>Score</th></tr>"
    if len(highscores) > 0:
        i = 1
        for x in highscores:
            username, score = tuple(x)
            out += "<tr><td>" + str(i) + ".</td><td width='80px'>" + str(username) + "</td><td>" + str(
                score) + "</td></tr>"
            i += 1
    return jsonify(data=out)


@app.route('/cam')
def cam():
    if configs['camera'] and check_permission('camera'):
        return render_with_nav('cam')
    else:
        abort(423)


@app.route('/countdown')
def countdown():
    return render_with_nav('countdown')


@app.route('/video_feed/<cam_id>')
def video_feed(cam_id='0'):
    if (not configs['camera']) or (not cam_id.isnumeric()) or (int(cam_id) not in cams):
        return
    """Video streaming route. Put this in the src attribute of an img tag."""
    if check_permission('camera'):
        video_cameras = [VideoCamera('0', use_detection=False)]

        def gen_camera(camera):
            """Video streaming generator function."""
            while True:
                frame = camera.get_frame()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        return Response(stream_with_context(gen_camera(video_cameras[int(cam_id)])),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/admin/console')
def console():
    if not check_permission('all'):
        abort(423)
    current_screen.enable_logs()

    def gen():
        while 1:
            try:
                if current_screen.logs is not None:
                    for i in current_screen.logs:
                        if '/admin/console' in str(i):
                            continue
                        data = {
                            'timestamp': str(datetime.now().time().strftime('%H:%M:%S')),
                            'content': escape(str(i)).splitlines(True)
                        }
                        yield "data:" + json.dumps(data) + "\n\n"
                    break
            except ValueError or TypeError:
                current_screen.disable_logs()
                current_screen.enable_logs()

    return Response(gen(), mimetype='text/event-stream')


@app.route('/admin/console/send', methods=['GET', 'POST'])
def send_command():
    if not check_permission('all'):
        abort(423)
    if request.method == 'POST':
        command = request.form['command']
        current_screen.send_commands(command)
    return Response('<!DOCTYPE html><html>'
                    '<head></head><body style="margin: 0">'
                    '<label for="command">Send command</label>'
                    '<form method="POST" style="width: 100%">'
                    '<input id="command" name="command" type="text" style="'
                    'width: 89.4%; '
                    'border-color: black; '
                    'color: greenyellow; '
                    'background-color: black;'
                    '" autocomplete="off" />'
                    '<input type="submit" style="width: 10%;background-color: #CCCCCC;"/>'
                    '</form>'
                    '</body></html>')


@app.route('/contact', methods=['GET', 'POST'])
@app.route('/contact?<remove>')
def contact(remove=-1):
    messages = []
    if check_permission('all'):
        with open('./contact.json', 'r+') as file:
            json_obj = json.load(file)
            if len(json_obj) > int(remove) >= 0:
                json_obj.pop(int(remove))
                file.seek(0)
                json.dump(json_obj, file, indent=2)
                messages.append({'type': 'success', 'head': 'Success!', 'text': 'removed message'})
            return render_with_nav('admin_contact', contact=json_obj, messages=messages)
    message = {'type': 'success', 'text': '', 'head': 'Success!'}
    form = None
    if request.method == 'POST':
        try:
            data = {'subject': request.form['subject'], 'message': request.form['message']}
            if check_permission('any'):
                user = user_for_name(session['username'])
                user = user.to_dict()
                user.pop('password')
                user.pop('permissions')
                data['userdata'] = user
            else:
                data['userdata'] = {
                    'firstname': request.form['firstname'],
                    'lastname': request.form['lastname'],
                    'email': request.form['email']
                }
            with open('./contact.json', 'r+') as f:
                json_obj = json.load(f)
                f.seek(0)
                data['id'] = len(json_obj)
                json_obj.append(data)
                json.dump(json_obj, f, indent=2)
                f.close()
                message['text'] = 'Successfully sent'
        except Exception as e:
            message['type'] = 'alert'
            message['head'] = 'Alert!'
            message['text'] = 'An error occurred'
            form = request.form

    if len(message['text']) > 0:
        messages.append(message)

    return render_with_nav('contact', loggedin=check_permission('any'), messages=messages, form=form)


@app.route('/get_contact_msgs', methods=['POST'])
def get_contact_msgs():
    key = 'Yd%ouVH@BB@JF#5kKjH8ipTt@qrYjZye'
    if request.method == 'POST':
        if request.form['key'] == key:
            with open('./contacts.json') as f:
                return Response(response=f.read(), mimetype='application/json')
    abort(423)


@app.route('/webspace')
def webspace():
    if check_permission('nwtk'):
        return redirect('https://projekte.tgm.ac.at/2dhit/gburkl/')
    else:
        abort(423)


@app.route('/github')
def github():
    return redirect('https://github.com/Minecraftschurli')


@app.route('/twitch')
def twitch():
    return redirect('https://www.twitch.tv/minecraftschurli')


@app.route('/twitter')
def twitter():
    return redirect('https://twitter.com/schurlibub')


@app.route('/<name>', methods=['POST', 'GET'])
def where(name):
    if name in routes:
        return render_with_nav(name)
    else:
        abort(404)


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
    if 'username' in session and valid_user(session['username']):
        nav_out.append(('Logout', '/logout', False, False))
    else:
        nav_out.append(('Login', '/login', False, False))

    return nav_out


def render_with_nav(name, **kwargs):
    return render_template(name + ".html", nav=get_nav(name), **kwargs)


def check_permission(permission):
    return 'username' in session and valid_user(session['username']) and has_user_permission(permission, user_for_name(
        session['username']))


def user_for_name(name):
    return users[name]


def has_user_permission(permission, user):
    return permission in user.permissions or "all" in user.permissions


def valid_login(name, password):
    if name in users:
        return bcrypt.check_password_hash(users[name].password.encode('utf-8'), password)
    return False


def add_user(fname, lname, name, password, email, permissions=None):
    if permissions is None:
        permissions = list()
    if name not in users:
        if email == (name + '@student.tgm.ac.at') and not ('nwtk' in permissions):
            permissions.append('nwtk')
        users[name] = User(fname, lname, name, bcrypt.generate_password_hash(password).decode('utf-8'), email,
                           permissions)
        return True
    else:
        return False


def remove_user(user):
    if user in users:
        users.pop(user)
        return True
    return False


def valid_user(user):
    return user is not None and user is not "" and user in users


def load_users():
    global users
    with open(configs['users'], 'r') as users_file:
        json_array = json.load(users_file)
        user_tmp = dict()
        for user in json_array:
            user_tmp[user['username']] = User(user['firstname'], user['lastname'], user['username'], user['password'],
                                              user['email'], user['permissions'])
        users = user_tmp.copy()


def save_users():
    with open(configs['users'], 'w') as users_file:
        data = list()
        for _, user in users.items():
            data.append(user.to_dict())
        json.dump(data, users_file, indent=4)


load_users()

if __name__ == '__main__':
    def is_list(value):
        return isinstance(value, list)

    app.jinja_env.filters.update({
        'is_list': is_list,
    })
    if platform.system() is not 'Windows':
        meinheld.listen(('0.0.0.0', 80))
        meinheld.run(app)
    else:
        app.run(None, 80, False, threaded=True)
