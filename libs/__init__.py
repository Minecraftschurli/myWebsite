import json
import sys

from flask import Flask
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy

from .logger import Logger

db = SQLAlchemy()

nav = list()
configuration = dict()

get_user_manager = None


def create_app():
    global configuration, nav, db, user_manager, get_user_manager

    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    nav = json.load(open('./nav.json'))
    configuration = json.load(open('./conf.json'))

    app.secret_key = bytes(configuration['secret_key'], 'UTF-8')

    for k, v in configuration['app_configurations'].items():
        app.config[k] = v

    db.init_app(app)

    # from . import databases
    # db.create_all(app=app)

    from .databases import User, Role
    from .customization import CustomUserManager
    user_manager = CustomUserManager(app, db, User, RoleClass=Role)
    app.user_manager = user_manager

    def _get_user_manager():
        return user_manager

    get_user_manager = _get_user_manager

    # app.app_context().push()
    # user = User.query.filter_by(email='minecraftschurli@gmail.com').first()
    # user.roles.append(Role(name='admin'))
    # db.session.commit()

    # Create all database tables
    # db.drop_all(app=app)
    # db.create_all(app=app)

    # @login_manager.user_loader
    # def user_for_name(name: str) -> User:
    #     return User.query.get(name)

    # blueprint for auth routes in our app
    # from .auth import auth as auth_blueprint
    # app.register_blueprint(auth_blueprint)

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

    from libs.functions import get_nav

    def get_current_user():
        return current_user

    app.add_template_global(get_nav, name='get_nav')
    app.add_template_global(isinstance, name='isinstance')
    app.add_template_global(get_current_user, name='get_current_user')

    sys.stderr = Logger(sys.stderr)
    sys.stdout = Logger(sys.stdout)

    return app
