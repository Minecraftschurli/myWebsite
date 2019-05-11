import json
import sys

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from .logger import Logger

bcrypt = Bcrypt()
login_manager = LoginManager()
db = SQLAlchemy()

nav = list()
configuration = dict()


def create_app():
    global configuration, nav, bcrypt, login_manager, db

    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    nav = json.load(open('./nav.json'))
    configuration = json.load(open('./conf.json'))

    app.secret_key = bytes(configuration['secret_key'], 'UTF-8')

    app.config['USE_SESSION_FOR_NEXT'] = configuration['USE_SESSION_FOR_NEXT']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = configuration['SQLALCHEMY_TRACK_MODIFICATIONS']
    app.config['SQLALCHEMY_DATABASE_URI'] = configuration['SQLALCHEMY_DATABASE_URI']

    bcrypt.init_app(app)
    db.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .databases import User

    @login_manager.user_loader
    def user_for_name(name: str) -> User:
        return User.query.get(name)

    # blueprint for auth routes in our app
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # blueprint for games parts of app
    from .games import games as games_blueprint
    app.register_blueprint(games_blueprint)

    # blueprint for admin parts of app
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)

    # blueprint for camera parts of app
    from .camera import camera as camera_blueprint
    app.register_blueprint(camera_blueprint)

    # blueprint for non auth, games, admin or camera parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    def is_list(value):
        return isinstance(value, list)

    with open('./log.txt', "w"):
        pass

    app.jinja_env.filters.update({
        'is_list': is_list
    })

    sys.stderr = Logger(sys.stderr)
    sys.stdout = Logger(sys.stdout)

    return app
