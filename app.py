# import functools
# import platform
# import sys
# from datetime import datetime
# from os.path import getsize
# from urllib.parse import urlparse, urljoin
#
# import requests
# from flask import *
# from flask_bcrypt import *
# from flask_login import LoginManager, login_required, current_user, login_user, logout_user
# from flask_sqlalchemy import SQLAlchemy
#
# from libs import adresslistenGenerator
# from libs.camera import VideoCamera
# from libs.databases import User, IPBlacklist, Contact, ShootItData
# from libs.logger import Logger
#
# app = Flask(__name__)
#
#
# def load_config():
#     with open('./conf.json', 'r') as conf:
#         configs = dict()
#         json_obj = json.load(conf)
#         for k, v in json_obj.items():
#             configs[k] = v
#         return configs
#
#
# configuration = load_config()
#
# app.config['USE_SESSION_FOR_NEXT'] = configuration['USE_SESSION_FOR_NEXT']
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = configuration['SQLALCHEMY_TRACK_MODIFICATIONS']
# app.config['SQLALCHEMY_DATABASE_URI'] = configuration['SQLALCHEMY_DATABASE_URI']
#
# bcrypt = Bcrypt(app)
# login_manager = LoginManager(app)
# db = SQLAlchemy(app)
#
# app.secret_key = bytes(configuration['secret_key'], 'UTF-8')
# login_manager.login_view = 'login'
#
# routes = [""]
# cams = [0]
#
# logfile = './log.txt'
#
# cur_size = 0
#
# nav = [("Home", "/", "any", False),
#        ("Projects", [
#            ("Superheroes X", "/sx", "any", False),
#            ("ShootIt", "/games/shootit", "any", False),
#            ("ITBoy", "/games/itboy", "any", False),
#            ("Adresslistengenerator", "/adr_gen", ("school", "adr_gen"), False)
#        ], "any", False),
#        ("Links", [
#            ("GitHub <i class='fab fa-github' style='font-size: 120%;'></i>", "/github", "any", True),
#            ("Twitch <i class='fab fa-twitch' style='font-size: 120%;color: purple'></i>", "/twitch", "any", True),
#            ("Twitter <i class='fab fa-twitter' style='font-size: 120%;color: #55ACEE'></i>", "/twitter", "any", True),
#            ("TGM - Projektserver", "/webspace", "school", True)
#        ], "any", False),
#        ("Contact", "/contact", "any", False),
#        ("Cam", "/cam", "camera", False),
#        ("Admin", "/admin", "all", False)]
#
# shootit_data = ShootItData()
#
#
# # decorators
# def permission_required(permission='any'):
#     def decorator(func):
#         if permission is not 'any':
#             func = login_required(func)
#
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             if (permission is 'login' or permission is 'any') or check_permission(permission):
#                 return func(*args, **kwargs)
#             else:
#                 return login_manager.unauthorized()
#         return wrapper
#     return decorator
#
#
# def check_ip(func):
#     @functools.wraps(func)
#     def wrapper(*args, **kwargs):
#         if _check_ip():
#             return func(*args, **kwargs)
#         else:
#             abort(423)
#     return wrapper
#
#
# # functions
# def blacklist_ip(ip_addr):
#     new_bl_ip = IPBlacklist(ip=ip_addr)
#     db.session.add(new_bl_ip)
#     db.session.commit()
#
#
# def _check_ip():
#     result = IPBlacklist.query.filter_by(ip=request.remote_addr).first()
#     if result:
#         return False
#     else:
#         return True
#
#
# def get_nav(name):
#     name = '/' + name
#     nav_out = list()
#     for n, d, p, e in nav:
#         if p == 'any' or (check_permission(p)):
#             if type(d) is list:
#                 projects_out = list()
#                 for n1, d1, p1, e1 in d:
#                     if p1 == 'any' or (check_permission(p1)):
#                         projects_out.append((n1, d1, e1))
#                 nav_out.append((n, projects_out, False, False))
#             else:
#                 nav_out.append((n, d, name == d, e))
#     if current_user.is_authenticated:
#         nav_out.append(('Logout', '/logout', False, False))
#     else:
#         nav_out.append(('Login', '/login', False, False))
#
#     return nav_out
#
#
# def render_with_nav(name, **kwargs):
#     return render_template(name + ".html", nav=get_nav(name), **kwargs)
#
#
# def check_permission(permission):
#     return current_user.is_authenticated and current_user.has_permission(permission)
#
#
# def valid_login(name, password):
#     if valid_user(name):
#         return login_manager.user_callback(name).authenticate(password)
#     return False
#
#
# def add_user(fname, lname, name, password, email, permissions=None):
#     if permissions is None:
#         permissions = list()
#
#     if User.query.filter_by(email=email).first():
#         return False, 'email'
#     elif User.query.filter_by(username=name).first():
#         return False, 'username'
#
#     if email == (name + '@student.tgm.ac.at') and not ('school' in permissions):
#         permissions.append('school')
#     # noinspection PyArgumentList
#     new_user = User(first_name=fname, last_name=lname, username=name,
#                     password_hash=bcrypt.generate_password_hash(password).decode('utf-8'), email=email,
#                     permissions=', '.join(permissions))
#     # add the new user to the database
#     db.session.add(new_user)
#     db.session.commit()
#     return True, None
#
#
# def remove_user(name):
#     user = User.query.get(name)
#     if user:
#         db.session.delete(user)
#         db.session.commit()
#         return True
#     return False
#
#
# def valid_user(user):
#     return user is not None and user is not "" and User.query.get(user)
#
#
# def is_safe_url(target):
#     if 'console' in target:
#         return False
#     ref_url = urlparse(request.host_url)
#     test_url = urlparse(urljoin(request.host_url, target))
#     return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
#
#
# # auth
# @app.route('/login')
# @check_ip
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     return render_with_nav('login')
#
#
# @app.route('/login', methods=['POST'])
# @check_ip
# def login_post():
#     remember = True if 'remember' in request.form and request.form['remember'] else False
#
#     # check if user actually exists
#     # take the user supplied password, hash it, and compare it to the hashed password in database
#     if not valid_login(request.form['username'], request.form['password']):
#         flash({'text': 'Please check your login details and try again.', 'head': 'Error!'}, 'alert')
#         return redirect(url_for('login'))  # if user doesn't exist or password is wrong, reload the page
#
#     # if the above check passes, then we know the user has the right credentials
#     login_user(login_manager.user_callback(request.form['username']), remember=remember)
#     next_page = session['next']
#     # is_safe_url should check if the url is safe for redirects.
#     # See http://flask.pocoo.org/snippets/62/ for an example.
#     if not is_safe_url(next_page):
#         return redirect(url_for('index'))
#
#     return redirect(next_page or url_for('index'))
#
#
# @app.route('/signup')
# @check_ip
# def signup():
#     return render_with_nav('signup', code=None)
#
#
# @app.route('/signup', methods=['POST'])
# @check_ip
# def signup_post():
#     code = None
#     if not ('email' in request.form and request.form['email']):
#         code = "No email!"
#     elif not ('password' in request.form and 'password-repeat' in request.form and request.form['password'] ==
#               request.form['password-repeat']):
#         code = "Passwords do not match!"
#     else:
#         ret, c = add_user(request.form['firstname'], request.form['lastname'], request.form['username'],
#                           request.form['password'], request.form['email'])
#         if not ret:
#             if not ('username' in request.form and c is 'username'):
#                 code = "A User with this Username already exists!"
#             elif not (c is 'email'):
#                 code = "Only one Account per Email is allowed!"
#         else:
#             # save_users()
#             # load_users()
#             return redirect(url_for('login'))
#     flash({'head': 'Error!', 'text': code}, 'alert')
#     return render_with_nav('signup')
#
#
# @app.route('/logout')
# @check_ip
# def logout():
#     # remove the username from the session if it's there
#     logout_user()
#     return redirect(url_for('index'))
#
#
# # games
# @app.route('/games/shootit')
# @check_ip
# def shootit():
#     if not current_user.is_anonymous:
#         data = shootit_data.get_data_for_user(current_user.username)
#         if data is None:
#             shootit_data.create_and_get_user(current_user.username, assoc=current_user.username)
#     return render_with_nav('game', game_name='ShootIt', game_src='../static/games/shootit/game.html')
#
#
# @app.route('/games/itboy')
# @check_ip
# def itboy():
#     return render_with_nav('game', game_name='ITBoy', game_src='../static/games/itboy/ITBoy.html',
#                            game_settings=""
#                                          "aside {width: 100%;position: relative;overflow: hidden;max-width: 100%;}"
#                                          "main {overflow-y: scroll;width: 1027px;min-width: 1027px;position: "
#                                          "relative;padding: 10px} "
#                                          "#fullscreen {display: none;}"
#                                          ".iframe-cont iframe {border: inset 2px;height: 99.5%;width: 99%;resize: "
#                                          "none;} "
#                                          ".iframe-cont {resize: none;padding-bottom: 4px;}")
#
#
# @app.route('/static/games/shootit/GetOrCreateUserProfile?<opt>', methods=["POST"])
# @app.route('/static/games/shootit/GetOrCreateUserProfile', methods=["POST"])
# @check_ip
# def get_or_create_user_profile(opt=""):
#     c = False
#     new = False
#     if not current_user.is_anonymous:
#         data = shootit_data.get_data_for_user(current_user.username)
#         if data is None:
#             data = shootit_data.create_and_get_user(request.form['username'], assoc=current_user.username)
#         c = True
#     elif opt != "nocreate" and 'username' in request.form:
#         if shootit_data.user_exists(request.form['username']):
#             data = shootit_data.get_anonymus_user(request.form['username'])
#         else:
#             data = shootit_data.create_and_get_user(request.form['username'])
#             new = True
#         c = True
#     else:
#         data = {}
#     if isinstance(data, ShootItData.PerUser):
#         data = {
#             'username': data.username,
#             'easy': data.score_easy,
#             'medium': data.score_medium,
#             'hard': data.score_hard,
#             'impossible': data.score_impossible,
#             'linked': data.linked
#         }
#     return jsonify(**data, check=c, new=new)
#
#
# @app.route('/static/games/shootit/UpdateUserProfile', methods=["POST"])
# @check_ip
# def update_user_profile():
#     shootit_data.update(request.form['user'], request.form['difficulty'], request.form['score'])
#     return Response()
#
#
# @app.route('/static/games/shootit/highscore', methods=["POST"])
# @check_ip
# def get_highscores():
#     highscores = shootit_data.get_highscores(request.form['difficulty'])
#     out = "<tr><th>Nr.</th><th width='80px'>Name</th><th>Score</th></tr>"
#     if len(highscores) > 0:
#         i = 1
#         for x in highscores:
#             username, score = tuple(x)
#             out += "<tr><td>" + str(i) + ".</td><td width='80px'>" + str(username) + "</td><td>" + str(
#                 score) + "</td></tr>"
#             i += 1
#     return jsonify(data=out)
#
#
# # main
# @app.route('/')
# @check_ip
# def index():
#     return render_template("home.html", nav=get_nav(""))
#
#
# @app.route('/admin')
# @permission_required('all')
# @check_ip
# def admin():
#     users = User.query.all()
#     users = [u for u in sorted(users, key=lambda x: x.username.lower())]
#     return render_with_nav('admin/admin', users=users, config=configuration)
#
#
# @app.route('/admin/<command>', methods=['POST', 'GET'])
# @app.route('/admin/remove_user/<param>', methods=['POST', 'GET'])
# @permission_required(permission='all')
# @check_ip
# def admin_commands(command='remove_user', param=''):
#     messages = []
#
#     def edit_user_permissions(_=None):
#         user = User.query.get(request.form['username'])
#         if 'username' in request.form and 'permissions' in request.form and user:
#             user.permissions = ', '.join(str(request.form['permissions']).splitlines())
#             db.session.commit()
#             messages.append(
#                 {'type': 'success', 'text': 'Edited user permissions for user: ' + user.username, 'head': 'Success!'})
#
#     def toggle_camera(_=None):
#         configuration['camera']['status'] = (not configuration['camera']['status'])
#         messages.append(
#             {'type': 'success',
#             'text': 'Turned camera ' + ('on' if configuration['camera']['status'] else 'off') + '!',
#              'head': 'Success!'})
#
#     def toggle_detect(_=None):
#         configuration['camera']['use_detect'] = (not configuration['camera']['use_detect'])
#         messages.append({'type': 'success', 'text': 'Turned camera face detection ' + (
#             'on' if configuration['camera']['use_detect'] else 'off') + '!', 'head': 'Success!'})
#
#     # def reload_config(_=None):
#     #     save_config()
#     #     load_config()
#     #     messages.append({'type': 'success', 'text': 'Reloaded config!', 'head': 'Success!'})
#
#     def nothing(_=None):
#         pass
#
#     def _remove_user(user):
#         if remove_user(user):
#             messages.append({'type': 'success', 'text': 'removed user', 'head': 'Success!'})
#         else:
#             messages.append({'type': 'alert', 'text': 'removed user', 'head': 'Fail!'})
#
#     {
#         "edit_user_permissions": edit_user_permissions,
#         "remove_user": _remove_user,
#         "toggle_camera": toggle_camera,
#         "toggle_detect": toggle_detect,
#         # "reload_config": reload_config
#     }.get(command, nothing)(param)
#     for m in messages:
#         m_type = m['type']
#         m.pop('type')
#         flash(m, m_type)
#     return redirect(url_for('admin'))
#
#
# @app.route('/adr_gen', methods=['POST', 'GET'])
# @permission_required('school')
# @check_ip
# def adr_gen():
#     ta = ["", ""]
#     if request.method == 'POST':
#         ip = ".".join((
#             str(adresslistenGenerator.get_byte(request.form['firstByte'])),
#             str(adresslistenGenerator.get_byte(request.form['secondByte'])),
#             str(adresslistenGenerator.get_byte(request.form['thirdByte'])),
#             str(adresslistenGenerator.get_byte(request.form['fourthByte']))
#         ))
#         server_names = str(request.form["sName"]).replace(" ", "").splitlines()
#         client_names = str(request.form["cName"]).replace(" ", "").splitlines()
#         html = adresslistenGenerator.create(server_names, client_names, ip, int(request.form['snm'])).to_html()
#         rows = html.splitlines()
#
#         for e in rows:
#             rows[rows.index(e)] = len(e)
#
#         ta[0] = len(rows)
#         ta[1] = max(rows)
#     else:
#         html = None
#
#     s = '<style>\nul{\nmargin-top: 0;\nlist-style-type: none;\n}\nh4{\nmargin-top: ' \
#         '2px;\nmargin-bottom: 5px;\n}\n</style>\n'
#     return render_with_nav("adr_gen", request=request, out=html, calc_needles=adresslistenGenerator.calc_needles,
#                               ta=ta, style=s)
#
#
# @app.route('/sx')
# @check_ip
# def sx():
#     json_obj = json.loads(str(requests.get('https://api.cfwidget.com/minecraft/mc-mods/Superheroes-X')
#                               .content.decode('UTF-8')))
#     datetime_obj = datetime.strptime(json_obj['download']['uploaded_at']['date'], '%Y-%m-%d %H:%M:%S.%f')
#     json_obj['download']['uploaded_at']['date'] = datetime_obj.strftime('%b %d, %Y')
#     datetime_obj = datetime.strptime(json_obj['created_at'], '%Y-%m-%dT%H:%M:%SZ')
#     json_obj['created_at'] = datetime_obj.strftime('%b %d, %Y')
#     return render_with_nav('sx', info=json_obj)
#
#
# @app.route('/cam')
# @permission_required('camera')
# @check_ip
# def cam():
#     if configuration['camera']['status']:
#         return render_with_nav('cam')
#     else:
#         abort(404)
#
#
# @app.route('/countdown')
# @check_ip
# def countdown():
#     return render_with_nav('countdown')
#
#
# @app.route('/video_feed/<cam_id>')
# @permission_required('camera')
# @check_ip
# def video_feed(cam_id='0'):
#     if (not configuration['camera']['status']) or (not cam_id.isnumeric()) or (int(cam_id) not in cams):
#         abort(404)
#     """Video streaming route. Put this in the src attribute of an img tag."""
#     video_cameras = [VideoCamera('0', use_detection=configuration['camera']['use_detect'])]
#
#     def gen_camera(camera):
#         """Video streaming generator function."""
#         while True:
#             frame = camera.get_frame()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#     return Response(stream_with_context(gen_camera(video_cameras[int(cam_id)])),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')
#
#
# @app.route('/admin/console')
# @permission_required('all')
# @check_ip
# def console():
#     global last_size, cur_size
#     cur_size = getsize(logfile)
#     data = {'content': []}
#     if cur_size != last_size:
#         with open(logfile, 'r') as f:
#             f.seek(last_size if cur_size > last_size else 0)
#             text = f.read()
#             f.close()
#             last_size = cur_size
#             data['content'] = escape(text).splitlines(True)
#             for i in range(len(data['content'])):
#                 if '/admin/console' in data['content'][i]:
#                     data['content'].pop(i)
#
#     return Response(json.dumps(data))
#
#
# # noinspection PyBroadException
# @app.route('/contact', methods=['GET', 'POST'])
# @app.route('/contact?<remove>')
# @check_ip
# def contact(remove=-1):
#     messages = []
#     if check_permission('all'):
#         msgs = Contact.query.all()
#         if len(msgs) >= int(remove) > 0:
#             db.session.delete(Contact.query.get(int(remove)))
#             db.session.commit()
#             messages.append({'type': 'success', 'head': 'Success!', 'text': 'Deleted message!'})
#             for m in messages:
#                 m_type = m['type']
#                 m.pop('type')
#                 flash(m, m_type)
#             return redirect(url_for('contact'))
#         for m in messages:
#             m_type = m['type']
#             m.pop('type')
#             flash(m, m_type)
#         return render_with_nav('admin/admin_contact', contact=msgs)
#     message = {'type': 'success', 'text': '', 'head': 'Success!'}
#     form = None
#     if request.method == 'POST':
#         try:
#             data = {
#                 'subject': request.form['subject'],
#                 'message': request.form['message']
#             }
#             if check_permission('any'):
#                 user = current_user.to_dict()
#                 user.pop('password_hash')
#                 user.pop('permissions')
#                 user.pop('username')
#                 data.update(user)
#             else:
#                 data.update({
#                     'first_name': request.form['firstname'],
#                     'last_name': request.form['lastname'],
#                     'email': request.form['email']
#                 })
#             new_contact_request = Contact(**data)
#             db.session.add(new_contact_request)
#             db.session.commit()
#             message['text'] = 'Successfully sent'
#         except Exception:
#             message['type'] = 'alert'
#             message['head'] = 'Alert!'
#             message['text'] = 'An error occurred'
#             form = request.form
#
#     if len(message['text']) > 0:
#         messages.append(message)
#     for m in messages:
#         m_type = m['type']
#         m.pop('type')
#         flash(m, m_type)
#     return render_with_nav('contact', loggedin=check_permission('any'), form=form)
#
#
# @app.route('/get_contact_msgs', methods=['POST'])
# @check_ip
# def get_contact_msgs():
#     key = 'Yd%ouVH@BB@JF#5kKjH8ipTt@qrYjZye'
#     if request.method == 'POST':
#         if request.form['key'] == key:
#             with open('./contacts.json') as f:
#                 return Response(response=f.read(), mimetype='application/json')
#     abort(423)
#
#
# @app.route('/webspace')
# @permission_required('school')
# @check_ip
# def webspace():
#     return redirect('https://projekte.tgm.ac.at/2dhit/gburkl/')
#
#
# @app.route('/github')
# @check_ip
# def github():
#     return redirect('https://github.com/Minecraftschurli')
#
#
# @app.route('/twitch')
# @check_ip
# def twitch():
#     return redirect('https://www.twitch.tv/minecraftschurli')
#
#
# @app.route('/twitter')
# @check_ip
# def twitter():
#     return redirect('https://twitter.com/schurlibub')
#
#
# @app.route('/<name>')
# @check_ip
# def where(name):
#     if name in routes:
#         return render_with_nav(name)
#     elif 'php' in name:
#         blacklist_ip(request.remote_addr)
#         abort(423)
#     else:
#         abort(404)
#
#
# @login_manager.user_loader
# def user_for_name(name: str) -> User:
#     return User.query.get(name)  # users.get(name, None)
#
#
# # load_users()
#
# if platform.system() is not 'Windows':
#     import meinheld
#
#
# def main():
#     global last_size
#
#     # db.create_all(app=app)
#
#     # with open(configs['users'], 'r') as users_file:
#     #     json_array = json.load(users_file)
#     #     for user in json_array:
#     #         if User.query.get(user['username']):
#     #             continue
#     #         user['permissions'] = ', '.join(user['permissions'])
#     #         new_user = User(**user)
#     #         print(new_user)
#     #         # add the new user to the database
#     #         db.session.add(new_user)
#     #         db.session.commit()
#
#     def is_list(value):
#         return isinstance(value, list)
#
#     with open('./log.txt', "w"):
#         pass
#
#     last_size = getsize(logfile)
#
#     app.jinja_env.filters.update({
#         'is_list': is_list
#     })
#
#     sys.stderr = Logger(sys.stderr)
#     sys.stdout = Logger(sys.stdout)
#     if platform.system() is not 'Windows':
#         meinheld.listen(('0.0.0.0', 80))
#         meinheld.run(app)
#     else:
#         app.run('0.0.0.0', 80, threaded=True, debug=True)

if __name__ == '__main__':
    # main()
    import platform
    from libs import create_app

    app = create_app()
    if platform.system() == 'Linux':
        import meinheld

        meinheld.listen(('0.0.0.0', 80))
        meinheld.run(app)
    else:
        app.run('0.0.0.0', 80, threaded=True)
