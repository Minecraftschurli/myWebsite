from flask import Blueprint, Response, jsonify

from libs.decorators import *
from libs.functions import *

games = Blueprint('games', __name__)

shootit_data = ShootItData()


@games.route('/games/shootit')
@check_ip
def shootit():
    if not current_user.is_anonymous:
        data = shootit_data.get_data_for_user(current_user.username)
        if data is None:
            shootit_data.create_and_get_user(current_user.username, assoc=current_user.username)
    return render_with_nav('game', game_name='ShootIt', game_src='../static/games/shootit/game.html')


@games.route('/games/itboy')
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


@games.route('/static/games/shootit/GetOrCreateUserProfile?<opt>', methods=["POST"])
@games.route('/static/games/shootit/GetOrCreateUserProfile', methods=["POST"])
@check_ip
def get_or_create_user_profile(opt=""):
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
    if isinstance(data, ShootItData.PerUser):
        data = {
            'username': data.username,
            'easy': data.score_easy,
            'medium': data.score_medium,
            'hard': data.score_hard,
            'impossible': data.score_impossible,
            'linked': data.linked
        }
    return jsonify(**data, check=c, new=new)


@games.route('/static/games/shootit/UpdateUserProfile', methods=["POST"])
@check_ip
def update_user_profile():
    shootit_data.update(request.form['user'], request.form['difficulty'], request.form['score'])
    return Response()


@games.route('/static/games/shootit/highscore', methods=["POST"])
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
