var score = 0;
var targetObj;
var running = false;
var difficulty = 0;
var difficultyIncrement = 1;
var missedShots = 5;
var game;
var highscores = {easy:0,medium:0,hard:0,impossible:0};
//var sound = new Audio('../../audio/gun.wav');
var username = "guest";
const update = "./UpdateUserProfile";
const getOrCreate = "./GetOrCreateUserProfile";
const getHighscore = "./highscore";

function startGame() {
    if (!running) {
        running = true;
        spawnAlgorythm();
    }
}

function spawnAlgorythm() {
    var target = $("#target img");
    var rand = (2000/100*randomNumber(4,10))-10*difficulty;
    targetObj.height = rand < 20 ? 20 : rand;
    targetObj.width = rand < 20 ? 20 : rand;
    target.css({
        height: targetObj.height+'px',
        width: targetObj.width+'px'
    });
    targetObj.x = randomNumber(0,Number($(document).width())-Number(target.width()));
    targetObj.y = randomNumber(0,Number($(document).height())-Number(target.height()));
    spawn();
    if(running)game = setTimeout(spawnAlgorythm,randomNumber(1000,3000)-Math.sqrt(difficulty));
}

function hitSquare(x,y,target) {
    //console.log("x: " + target.x + " y: " + target.y);
    if (target.y > y || target.x > x) {
        return false;
    }
    var w = target.width + target.x;
    var h = target.height + target.y;
    if (!(w < target.x || w > x)) {
        return false;
    }
    return h < target.y || h > y;

}

function hitRound(x,y,target){
    var ellw = target.width;
    if (ellw <= 0.0) {
        return false;
    }
    var normx = (x - target.x) / ellw - 0.5;
    var ellh = target.height;
    if (ellh <= 0.0) {
        return false;
    }
    var normy = (y - target.y) / ellh - 0.5;
    return (normx * normx + normy * normy) < 0.25;
}

function setValuesFromDifficulty(text) {
    var hs = $('#highscore').text();
    switch (text) {
        case "Easy":
            difficulty = 0;
            difficultyIncrement = 1;
            missedShots = 5;
            highscores.easy = hs;
            break;
        case "Medium":
            difficulty = 2;
            difficultyIncrement = 1;
            missedShots = 3;
            highscores.medium = hs;
            break;
        case "Hard":
            difficulty = 3;
            difficultyIncrement = 2;
            missedShots = 2;
            highscores.hard = hs;
            break;
        case "Impossible":
            difficulty = 4;
            difficultyIncrement = 2;
            missedShots = 1;
            highscores.impossible = hs;
            break;
    }
    setLives(missedShots);
}

function gameOver() {
    clearTimeout(game);
    var diff = $('#difficultyChoose');
    $('#target').css("visibility","hidden");
    $('#menu').css("visibility","visible");
    //diff.css("visibility","hidden");
    $('#start h2').text("Retry");
    running = false;
    var go = $('#gameOver');
    var top = ($(document).height()/2)-(go.outerHeight()/2), left = ($(document).width()/2)-(go.outerWidth()/2);
    go.css({
        top: top,
        left: left,
        visibility: "visible"
    });
    var hs = $('#highscore');
    var highscore = Number(hs.text());
    if (score > highscore) {
        var dif = diff.text()
        switch (dif.toLowerCase()) {
            case 'easy':
                highscores.easy = highscore;
                break;
            case 'medium':
                highscores.medium = highscore;
                break;
            case 'hard':
                highscores.hard = highscore;
                break;
            case 'impossible':
                highscores.impossible = highscore;
                break;
        }
        hs.text(score);
        if (username !== "guest")
            $.post(update,
                {
                user: username,
                score: score,
                difficulty: dif
            },function (data, status) {});
    }
    $('#score').text(0);
    setValuesFromDifficulty(diff.text());
    score = 0;
}

function setPos() {
    var menu = $('#menu');
    var top = ($(document).height()/2)-(menu.outerHeight(true)/2);
    var left = ($(document).width()/2)-(menu.outerWidth(true)/2);
    menu.css({
        top: top - 90,
        left: left
    });
    var go = $('#gameOver');
    top = ($(document).height()/2)-(go.outerHeight(true)/2);
    left = ($(document).width()/2)-(go.outerWidth(true)/2);
    go.css({
        top: top,
        left: left
    });/*
    var diff = $('#diff');
    top = 10;
    left = (($(document).width())-diff.width()-280);
    diff.css({
        top: top,
        left: left
    });*/
    var uname = $('#uname');
    top = ($(document).height()-uname.outerHeight()-10);
    left = (($(document).width())-uname.width()-20);
    uname.css({
        top: top,
        left: left
    });
    var hs = $('#hs');
    top = 15;
    left = (($(document).width())-hs.width()-60);
    hs.css({
        top: top,
        left: left
    });
    var hss = $('#highscores');
    top = 45;
    left = (($(document).width())-200);
    hss.css({
        top: top,
        left: left
    });
}

function setUser(){
    var c = false;
    var fin = false;
    do{
        var user = prompt("Please enter your name", "");
        if (user != null && user !== ""){
            username = user;
            $('#uname span').text(username);
        }
        if (username !== "guest")
            $.post(getOrCreate,{
                username: username
            }, function (data, status) {
                //data = JSON.parse(data);
                if (status === 'success' && data.check) {
                    if(data.new)alert('User does not exist!\nCreated new user!');
                    highscores.easy = Number(data.easy);
                    highscores.medium = Number(data.medium);
                    highscores.hard = Number(data.hard);
                    highscores.impossible = Number(data.impossible);
                    $('#login').css("visibility","hidden")
                } else {
                    c = false
                }
                fin = true
            });
        while (!fin);
    } while (c);
    setValuesFromDifficulty($('#difficultyChoose').text())
}

function updateHighscores(){
    $.post(getHighscore,{
        difficulty: $('#difficultyChoose').text()
    }, function (data, status) {
        $('#highscores table').html(data.data);
    });
    }

function updateRepeat(){
    updateHighscores();
    setTimeout(updateRepeat,100000);
}

function setLives(lives) {
    var o = '';
    for (let i = 0; i < lives; i++) {
        o += '<i class="fas fa-heart"></i>'
    }
    $('#lives').html(o);
}



$(document).ready(function () {
    $.post(getOrCreate+"?nocreate",{
            username: username
        }, function (data, status) {
            //data = JSON.parse(data);
            if (status === 'success' && data.check) {
                highscores.easy = Number(data.easy);
                highscores.medium = Number(data.medium);
                highscores.hard =Number(data.hard);
                highscores.impossible = Number(data.impossible);
                username = data.username;
                $('#uname span').text(data.username);
                var diff = $('#difficultyChoose').text();
                var hs = $('#highscore');
                switch (diff.toLowerCase()) {
                    case 'easy':
                        hs.text(highscores.easy);
                        break;
                    case 'medium':
                        hs.text(highscores.medium);
                        break;
                    case 'hard':
                        hs.text(highscores.hard);
                        break;
                    case 'impossible':
                        hs.text(highscores.impossible);
                        break;
                }
                setValuesFromDifficulty(diff);
                $('#login').css("visibility","hidden")
            }
        });

    setTimeout(setPos,10);
    updateRepeat();
    $(window).resize(setPos);
    $(document).resize(setPos);
    $(document).keypress(function (e) {
        if (e.which === 107) {
            gameOver();
        }
    });
    var target = $("#target");
    $(document).mousemove(function (e){
        $("#crosshair").css({left:e.pageX-50, top:e.pageY-50});
    });
    $(document).click(function (e) {
		/*sound.pause();
		sound.currentTime = 0;
		sound.play();*/
        var start = $('#start');
        var menu = $("#menu");
        var posS = start.offset();
        var diff = $('#difficultyChoose');
        var posD = diff.offset();
        var login = $('#login');
        var posL = login.offset();
        var hs = $('#highscore');

        function difficultyChanged() {
            var text = $('#difficultyChoose span');
            switch (text.text()) {
                case "Easy":        text.text("Medium");
                                    highscores.easy = Number(hs.text());
                                    difficulty = 2;
                                    difficultyIncrement = 1;
                                    missedShots = 3;
                                    hs.text(highscores.medium);
                                    diff.css("background-color","orange");
                                    break;
                case "Medium":      text.text("Hard");
                                    highscores.medium = Number(hs.text());
                                    difficulty = 3;
                                    difficultyIncrement = 2;
                                    missedShots = 2;
                                    hs.text(highscores.hard);
                                    diff.css("background-color","red");
                                    break;
                case "Hard":        text.text("Impossible");
                                    highscores.hard = Number(hs.text());
                                    difficulty = 4;
                                    difficultyIncrement = 2;
                                    missedShots = 1;
                                    hs.text(highscores.impossible);
                                    diff.css("background-color","darkred");
                                    break;
                case "Impossible":  text.text("Easy");
                                    highscores.impossible = Number(hs.text());
                                    difficulty = 0;
                                    difficultyIncrement = 1;
                                    missedShots = 5;
                                    hs.text(highscores.easy);
                                    diff.css("background-color","aquamarine");
                                    break;
            }
            setLives(missedShots);
            $("#difficulty").text(difficulty);
            updateHighscores();
        }

        if (hitRound(e.pageX,e.pageY,{x:posS.left, y:posS.top, width:start.outerWidth(), height:start.outerHeight()}) && menu.css("visibility") === "visible"){
            menu.css("visibility","hidden");
            $('#gameOver').css("visibility","hidden");
            startGame();
        } else if (hitRound(e.pageX, e.pageY, {x: posD.left, y: posD.top, width: diff.outerWidth(), height: diff.outerHeight()}) && menu.css("visibility") === "visible") {
            difficultyChanged();
        } else if (hitRound(e.pageX, e.pageY, {x: posL.left, y: posL.top, width: login.outerWidth(), height: login.outerHeight()})&& menu.css("visibility") === "visible") {
            setUser();
        } else if (hitRound(e.pageX,e.pageY,targetObj) && $("#target").css("visibility") === "visible"){
            score++;
            if (score % 25 === 0) {
                difficulty += difficultyIncrement;
                $("#difficulty").text(difficulty);
            }
            target.css("visibility","hidden");
            $("#score").text(score);
        } else if (running){
            missedShots--;
            setLives(missedShots);
            if (missedShots <= 0){
                gameOver();
            }
        }
    });
    targetObj = {
        x: 0,
        y: 0,
        width: 0,
        height: 0
    };
    $('#target img').css({
        "width":'0px',
        "height":'0px'
    });
});

function spawn() {
    $("#target").css({
        left: targetObj.x,
        top: targetObj.y,
        visibility: 'visible'
    });
}

function randomNumber(min, max) {
    return Math.random() * (max - min) + min;
}