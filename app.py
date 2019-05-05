import functools
import platform
import re
import sys
from datetime import datetime
from os.path import getsize
from urllib.parse import urlparse, urljoin

import requests
from flask import *
from flask_bcrypt import *
from flask_login import *  # LoginManager, login_required, current_user, login_user, logout_user

from libs.__init__ import User, adresslistenGenerator, ShootItData, VideoCamera

app = Flask(__name__)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

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

app.secret_key = bytes(configs['secret_key'], 'UTF-8')
login_manager.login_view = 'login'
app.config['USE_SESSION_FOR_NEXT'] = True

routes = [""]
cams = [0]

testfile = './log.txt'
last_size = getsize(testfile)

shootit_data = ShootItData()

users = dict()

cur_size = 0
ip_blacklist = []

nav = [("Home", "/", "any", False),
       ("Projects", [
           ("Superheroes X", "/sx", "any", False),
           ("ShootIt", "/games/shootit", "any", False),
           ("ITBoy", "/games/itboy", "any", False),
           ("Adresslistengenerator", "/adr_gen", ("school", "adr_gen"), False)
       ], "any", False),
       ("Links", [
           ("GitHub <i class='fab fa-github' style='font-size: 120%;'></i>", "/github", "any", True),
           ("Twitch <i class='fab fa-twitch' style='font-size: 120%;color: purple'></i>", "/twitch", "any", True),
           ("Twitter <i class='fab fa-twitter' style='font-size: 120%;color: #55ACEE'></i>", "/twitter", "any", True),
           ("TGM - Projektserver", "/webspace", "school", True)
       ], "any", False),
       ("Contact", "/contact", "any", False),
       ("Cam", "/cam", "camera", False),
       ("Admin", "/admin", "all", False)]


# functions
def permission_required(permission='any'):
    def decorator(func):
        if permission is not 'any':
            func = login_required(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if (permission is 'login' or permission is 'any') or check_permission(permission):
                return func(*args, **kwargs)
            else:
                return login_manager.unauthorized()

        return wrapper

    return decorator


def check_ip(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if _check_ip():
            return func(*args, **kwargs)
        else:
            abort(423)

    return wrapper


def blacklist_ip(ip_addr):
    ip_blacklist.append(ip_addr)


def _check_ip():
    return request.remote_addr not in ip_blacklist


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
    if name not in users:
        if email == (name + '@student.tgm.ac.at') and not ('school' in permissions):
            permissions.append('school')
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


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def load_users():
    global users
    with open(configs['users'], 'r') as users_file:
        json_array = json.load(users_file)
        user_tmp = dict()
        for user in json_array:
            user_tmp[user['username']] = User.from_dict(user)
        users = user_tmp.copy()


def save_users():
    with open(configs['users'], 'w') as users_file:
        data = list()
        for _, user in users.items():
            data.append(user.to_dict())
        json.dump(data, users_file, indent=4)


# auth
@app.route('/login')
@check_ip
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_with_nav('login')


@app.route('/login', methods=['POST'])
@check_ip
def login_post():
    remember = True if request.form['remember'] else False

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not valid_login(request.form['username'], request.form['password']):
        flash('Please check your login details and try again.')
        return redirect(url_for('login'))  # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(login_manager.user_callback(request.form['username']), remember=remember)
    next_page = session['next']
    # is_safe_url should check if the url is safe for redirects.
    # See http://flask.pocoo.org/snippets/62/ for an example.
    if not is_safe_url(next_page):
        return abort(400)

    return redirect(next_page or url_for('index'))


@app.route('/signup')
@check_ip
def signup():
    return render_with_nav('signup', code=None)


@app.route('/signup', methods=['POST'])
@check_ip
def signup_post():
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
    return render_with_nav('signup', code=code)


@app.route('/logout')
@check_ip
def logout():
    # remove the username from the session if it's there
    logout_user()
    return redirect(url_for('index'))


# games
@app.route('/games/shootit')
@check_ip
def shootit():
    shootit_data.refresh()
    if not current_user.is_anonymous:
        data = shootit_data.get_data_for_user(current_user.username)
        if data is None:
            shootit_data.create_and_get_user(current_user.username, assoc=current_user.username)
    return render_with_nav('game', game_name='ShootIt', game_src='../static/games/shootit/game.html')


@app.route('/games/itboy')
@check_ip
def itboy():
    return render_with_nav('game', game_name='ITBoy', game_src='../static/games/itboy/ITBoy.html',
                           game_settings=""
                                         "aside {width: 100%;position: relative;overflow: hidden;max-width: 100%;}"
                                         "main {overflow-y: scroll;width: 1027px;min-width: 1027px;position: "
                                         "relative;padding: 10px} "
                                         "#fullscreen {display: none;}"
                                         ".iframe-cont iframe {border: inset 2px;height: 99.5%;width: 99%;resize: "
                                         "none;} "
                                         ".iframe-cont {resize: none;padding-bottom: 4px;}")


@app.route('/static/games/shootit/GetOrCreateUserProfile?<opt>', methods=["POST"])
@app.route('/static/games/shootit/GetOrCreateUserProfile', methods=["POST"])
@check_ip
def get_or_create_user_profile(opt=""):
    shootit_data.refresh()
    c = False
    new = False
    if not current_user.is_anonymous:
        data = shootit_data.get_data_for_user(current_user.username)
        if data is None:
            data = shootit_data.create_and_get_user(request.form['username'], assoc=current_user.username)
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
@check_ip
def update_user_profile():
    shootit_data.update(request.form['user'], request.form['difficulty'], request.form['score'])
    return Response()


@app.route('/static/games/shootit/highscore', methods=["POST"])
@check_ip
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


# main
@app.route('/')
@check_ip
def index():
    return render_template("home.html", nav=get_nav(""))


@app.route('/admin')
@permission_required('all')
@check_ip
def admin():
    sorted_users = []
    for key in sorted(users.keys(), key=lambda x: x.lower()):
        sorted_users.append((key, users[key]))
    return render_with_nav('admin/admin', users=sorted_users, config=configs)


@app.route('/admin/<command>', methods=['POST', 'GET'])
@app.route('/admin/remove_user/<param>', methods=['POST', 'GET'])
@permission_required(permission='all')
@check_ip
def admin_commands(command='', param=''):
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

    def _remove_user(user):
        remove_user(user)
        reload_user()
        messages.append({'type': 'success', 'text': 'removed user', 'head': 'Success!'})

    {
        "reload_user": reload_user,
        "edit_user_permissions": edit_user_permissions,
        "remove_user": _remove_user,
        "toggle_camera": toggle_camera,
        "reload_config": reload_config
    }.get(command, nothing)(param)
    return render_template("admin/admin_messages.html", messages=messages)


@app.route('/adr_gen', methods=['POST', 'GET'])
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


@app.route('/sx')
@check_ip
def sx():
    json_obj = json.loads(str(requests.get('https://api.cfwidget.com/minecraft/mc-mods/Superheroes-X')
                              .content.decode('UTF-8')))
    datetime_obj = datetime.strptime(json_obj['download']['uploaded_at']['date'], '%Y-%m-%d %H:%M:%S.%f')
    json_obj['download']['uploaded_at']['date'] = datetime_obj.strftime('%b %d, %Y')
    datetime_obj = datetime.strptime(json_obj['created_at'], '%Y-%m-%dT%H:%M:%SZ')
    json_obj['created_at'] = datetime_obj.strftime('%b %d, %Y')
    return render_with_nav('sx', info=json_obj)


@app.route('/cam')
@permission_required('camera')
@check_ip
def cam():
    if configs['camera']:
        return render_with_nav('cam')
    else:
        abort(404)


@app.route('/countdown')
@check_ip
def countdown():
    return render_with_nav('countdown')


@app.route('/video_feed/<cam_id>')
@permission_required('camera')
@check_ip
def video_feed(cam_id='0'):
    if (not configs['camera']) or (not cam_id.isnumeric()) or (int(cam_id) not in cams):
        abort(404)
    """Video streaming route. Put this in the src attribute of an img tag."""
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
@permission_required('all')
@check_ip
def console():
    global last_size, cur_size
    cur_size = getsize(testfile)
    data = {'content': []}
    if cur_size != last_size:
        with open(testfile, 'r') as f:
            f.seek(last_size if cur_size > last_size else 0)
            text = f.read()
            f.close()
            last_size = cur_size
            data['content'] = escape(text).splitlines(True)
            for i in range(len(data['content'])):
                if '/admin/console' in data['content'][i]:
                    data['content'].pop(i)

    return Response(json.dumps(data))


# noinspection PyBroadException
@app.route('/contact', methods=['GET', 'POST'])
@app.route('/contact?<remove>')
@check_ip
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
            return render_with_nav('admin/admin_contact', contact=json_obj, messages=messages)
    message = {'type': 'success', 'text': '', 'head': 'Success!'}
    form = None
    if request.method == 'POST':
        try:
            data = {'subject': request.form['subject'], 'message': request.form['message']}
            if check_permission('any'):
                user = current_user
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
        except Exception:
            message['type'] = 'alert'
            message['head'] = 'Alert!'
            message['text'] = 'An error occurred'
            form = request.form

    if len(message['text']) > 0:
        messages.append(message)

    return render_with_nav('contact', loggedin=check_permission('any'), messages=messages, form=form)


@app.route('/get_contact_msgs', methods=['POST'])
@check_ip
def get_contact_msgs():
    key = 'Yd%ouVH@BB@JF#5kKjH8ipTt@qrYjZye'
    if request.method == 'POST':
        if request.form['key'] == key:
            with open('./contacts.json') as f:
                return Response(response=f.read(), mimetype='application/json')
    abort(423)


@app.route('/webspace')
@permission_required('school')
@check_ip
def webspace():
    return redirect('https://projekte.tgm.ac.at/2dhit/gburkl/')


@app.route('/github')
@check_ip
def github():
    return redirect('https://github.com/Minecraftschurli')


@app.route('/twitch')
@check_ip
def twitch():
    return redirect('https://www.twitch.tv/minecraftschurli')


@app.route('/twitter')
@check_ip
def twitter():
    return redirect('https://twitter.com/schurlibub')


@app.route('/<name>')
@check_ip
def where(name):
    if name in routes:
        return render_with_nav(name)
    elif 'php' in name:
        blacklist_ip(request.remote_addr)
        abort(423)
    else:
        abort(404)


@login_manager.user_loader
def user_for_name(name: str) -> User:
    return users.get(name, None)


load_users()

if platform.system() is not 'Windows':
    import meinheld

ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


class Logger(object):
    def __init__(self, _in):
        self.terminal = _in
        self.log = open("log.txt", "a")

    def write(self, message):
        self.terminal.write(message)
        if '/admin/console' not in message:
            self.log.write(ansi_escape.sub('', message))

    def flush(self):
        self.terminal.flush()
        self.log.flush()
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass


if __name__ == '__main__':
    def is_list(value):
        return isinstance(value, list)


    with open('./log.txt', "w"):
        pass

    app.jinja_env.filters.update({
        'is_list': is_list,
    })

    sys.stderr = Logger(sys.stderr)
    sys.stdout = Logger(sys.stdout)
    if platform.system() is not 'Windows':
        meinheld.listen(('0.0.0.0', 80))
        meinheld.run(app)
    else:
        app.run('0.0.0.0', 80, threaded=True, debug=True)
