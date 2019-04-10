class Settings{
    /*maxLife;
    steps;
    jumpHeight;
    gravity;
    Vspeed;
    Hspeed;*/

    constructor(){
        //this.maxLife = 200;
        this.steps = 3;
        this.jumpHeight = 2;
        this.gravity = 0.05;
        this.Vspeed = 5;
        this.Hspeed = 0.5;
    }
}

class Level {
    /*terrain;
    flagX;
    flagY;*/

    constructor(terrain,flagX,flagY,time){
        this.terrain = terrain;
        this.flagX = flagX;
        this.flagY = flagY;
        this.time = time;
    }
}

class ObjectContainer {
    //id;

    constructor(id) {
        this.id = '#'+id;
    }

    add(id, img){
        let imgTag;
        if (!types.includes(img))
            imgTag = '';
        else
            imgTag = '<img src="./'+img+'" alt="obj">';
        let tag = '<div id="'+id+'">'+imgTag+'</div>';
        $(this.id).append($(tag));
    }
}

class BoundingBox {
    /*width;
    height;
    posX;
    posY;*/

    constructor(width, height, posX, posY){
        this.width = width;
        this.height = height;
        this.posX = posX;
        this.posY = posY;
    }

    setPos(x,y){
        this.posY = y;
        this.posX = x;
    }
}

class Object {
    /*id;
    posX;
    posY;
    boundingBox;
    img;*/

    constructor(id,posX,posY){
        this.id = "#"+id;
        this.posX = posX;
        this.posY = posY;
        // noinspection JSJQueryEfficiency
        if (!$(this.id).length) {
            this.addMissing();
        }
        // noinspection JSJQueryEfficiency
        let elem = $(this.id);
        this.img = this.id+'>img';
        this.boundingBox = new BoundingBox(elem.width(),elem.height(),this.getPosXForCSS(),this.getPosYForCSS());
        this.updateCSS();
    }

    setPos(x,y){
        this.posY = y;
        this.posX = x;
        this.boundingBox.setPos(this.posX,this.posY);
        this.updateCSS();
    }

    updateCSS() {
        $(this.id).css({'top': this.getPosYForCSS(), 'left': this.getPosXForCSS()})
    }

    remove(){
        $(this.id).remove();
    }

    addMissing() {
        objCont.add(id);
    }

    getPosYForCSS() {
        return this.posY;
    }

    getPosXForCSS() {
        return this.posX;
    }

    getWidthForCSS() {
        return this.boundingBox.width;
    }

    getHeightForCSS() {
        return this.boundingBox.height;
    }
}

class Stehdings extends Object {
    constructor(id){
        super(id,0,0);
        objCont.add(id,'stehdings.png');
        objects.push(this);
        this.img = this.id+'>img';
        this.boundingBox = new BoundingBox(170/1620*1000,50/948*562,this.getPosXForCSS(),this.getPosYForCSS());
        this.updateCSS();
    }

    addMissing(){}

    updateCSS(){
        $(this.id).css({top: this.getPosYForCSS(), left: this.getPosXForCSS(), width: this.getWidthForCSS(), height: this.getHeightForCSS()})
    }
}

class Flag extends Object {
    constructor(id){
        super(id,0,0);
        objCont.add(id,'flag.gif');
        objects.push(this);
        this.img = this.id+'>img';
        this.boundingBox = new BoundingBox(50/1620*1000,80/948*562,this.getPosXForCSS(),this.getPosYForCSS());
        this.updateCSS();
    }

    addMissing(){}

    updateCSS(){
        $(this.id).css({top: this.getPosYForCSS(), left: this.getPosXForCSS(), width: this.getWidthForCSS(), height: this.getHeightForCSS()})
    }
}

class Entity extends Object {
    /*dead;
    life;*/

    constructor(id, posX, posY, life){
        super(id,posX,posY);
        if (life != null){
            this.life = life;
            this.maxLife = life;
        } else {
            this.life = 0;
            this.maxLife = 0;
        }
        this.dead = false;
    }

    damage(value){
        this.life -= value;
        if (this.life < 0) {
            this.life = 0;
            this.setDead(true);
        }
    }

    move(x,y){
        this.posY += y;
        this.posX += x;
        this.boundingBox.setPos(this.posX,this.posY);
        this.updateCSS();
    }

    setDead(dead){
        this.dead = dead;
    }

    isDead(){
        return this.dead;
    }
}

class Player extends Entity {
    //jumping;

    constructor(id,posX,posY){
        super(id,posX,posY,0);
        this.jumping = false;
    }

    setMaxLife(life){
        if (life < 0) return false;
        this.maxLife = life;
        return true;
    }

    move(x, y) {
        if (this.isDead()) return;
        for (let i = 0; i < ((x < 0) ? -x/settings.Hspeed : x/settings.Hspeed); i++) {
            if (!this.checkMove((x < 0) ? -settings.Hspeed : settings.Hspeed,0)){
                break;
            }
            super.move((x < 0) ? -settings.Hspeed : settings.Hspeed, y);
        }
        for (let i = 0; i < ((y < 0) ? -y/settings.Vspeed : y/settings.Vspeed); i++) {
            if (!this.checkMove(0,(y < 0) ? -settings.Vspeed : settings.Vspeed)){
                yVel = 0;
                break;
            }
            super.move(0, (y < 0) ? -settings.Vspeed : settings.Vspeed);
        }
        if (x > 0) $(this.img).css('transform', "scaleX(1)");
        else if (x < 0) $(this.img).css('transform', "scaleX(-1)");
    }

    damage(value) {
        super.damage(value);
        if (this.life <= 0 && !this.isDead()) this.setDead(true);
        change_lc(this.life);
    }

    setDead(dead) {
        if (dead){
            $(this.img).src = "ITBoy_dead.png";
            $('#next').hide();
            $('#menu_text').text('You Died!');
            $('#menu').show();
        }else {
            this.life = this.maxLife;
            this.damage(0);
            $(this.img).src = "ITboy2.gif";
            this.setPos(10,ground);
            //location.reload()
            /*
            change_lc(settings.maxLife * settings.restartFaktor);
            this.life = settings.maxLife * settings.restartFaktor;*/
        }
        super.setDead(dead);
    }

    jump(){
        if (!this.checkMove(0,-0.1)) return;
        if (this.isJumping()) return;
        /***********************************************************/
        /*                     Character Jump					   */
        /***********************************************************/
        this.move(0,yVel = -settings.jumpHeight)


        /***********************************************************/
    }

    isJumping(){
        this.jumping = !(this.boundingBox.posY === ground || this.collideDown());
        return this.jumping;
    }

    checkMove(x,y) {
        for (let i = 0; i < objects.length; i++) {
            let value = objects[i];
            if (value instanceof Player) continue;
            if (checkHitbox(value.boundingBox, new BoundingBox(this.boundingBox.width,this.boundingBox.height,this.boundingBox.posX+x,this.boundingBox.posY+y))) {
                if (value instanceof Flag) {
                    levelComplete();
                    return true;
                }
                return false;
            }
        }
        return this.boundingBox.posY + y <= ground;
    }

    collideDown() {
        for (let i = 0; i < objects.length; i++) {
            let value = objects[i];
            if (value instanceof Player) continue;
            if (checkHitbox(value.boundingBox, new BoundingBox(this.boundingBox.width,this.boundingBox.height,this.boundingBox.posX,this.boundingBox.posY+settings.Vspeed))) {
                return !(value instanceof Flag);
            }
        }
        return false;
    }
}


let right_key_down = false;
let left_key_down = false;
let jump_key_down = false;

const types = ['stehdings.png', 'flag.gif'];
let ground;
let player;
const settings = new Settings();
const objects = new Array(0);
let objCont = new ObjectContainer('objects');
let yVel = 0;
let complete = false;
let ticks = 0;
let id = 0;
let level = -1;
let levels = [];
let paused = false;


function applyGravity() {
    yVel += settings.gravity;
    if (!player.checkMove(0,yVel))
        yVel = 0;
    else
        player.move(0,yVel)
}

function tick() {
    if (paused) return;
    move();
    applyGravity();
    if (!complete) {
        if (ticks >= 10){
            ticks = 0;
            damage(3);
        }else ticks++;
    }
}

function move() {
    if (complete) return;
    if (right_key_down) {
        player.move(settings.steps,0);
    } else if (left_key_down) {
        player.move(-settings.steps,0);
    }
    if (jump_key_down) {
        player.jump();
    }
}

function repeat(){
    tick();
    setTimeout(repeat,10);
}


/***********************************************************/
/*                  Keyboard Listener					   */
/***********************************************************/
function KeyPressed(evt) {
    /*******************************************************/
    /*               Important KeyCodes                    */
    /*******************************************************/
    /*
     UP Arrow: KeyCode 38
     DOWN Arrow: KeyCode 40
     LEFT Arrow: KeyCode 37
     RIGHT Arrow: KeyCode 39
     SPACE: KeyCode 32
     W: 87
     S: 83
     A: 65
     D: 68
    */
    /*******************************************************/
    switch (evt.which) {
        //Debug
        case 88:
            damage(10);
            break;
        case 89:
            heal(10);
            break;
    }
}

function KeyDown(evt) {
    if (!player.isDead()){
        switch (evt.which) {
                //LEFT
            case 37:
            case 65:
                left_key_down = true;
                break;
                //RIGHT
            case 39:
            case 68:
                right_key_down = true;
                break;
            case 32:
                jump_key_down = true;
                break;
        }
    }
}

function KeyUp(evt) {
    switch (evt.which) {
        //LEFT
        case 37:
        case 65:
            left_key_down = false;
            break;
            //RIGHT
        case 39:
        case 68:
            right_key_down = false;
            break;
        case 32:
            jump_key_down = false;
            break;
    }
}
/***********************************************************/


/***********************************************************/
/*                  Collission Detect					   */
/***********************************************************/
function checkHitbox(bb0, bb1){
    let x = bb0.posX,
        y = bb0.posY,
        w = bb0.width,
        h = bb0.height,
        x0 = bb1.posX,
        y0 = bb1.posY,
        w0 = bb1.width,
        h0 = bb1.height;
    if (w <= 0 || h <= 0) {
        return false;
    }
    return ((((x + w) > x0) && (x < (x0 + w0))) && (((y + h) > y0) && (y < (y0 + h0))));
}

/***********************************************************/


/***********************************************************/
/*                  Life Counter                           */
/***********************************************************/
/*Live Counter - lc
    0-25   lp -> Rot	#ff0000
    26-50  lp -> Orange	#ff8000
    51-75  lp -> Gelb 	#ffff00
    76-100 lp -> Grün	#009900
*/
function change_lc(wert) {
    //
    let percent = wert / (player.maxLife / 100);

    //Konvertieren des Wertes in einen Zahlenwert
    //wert = Number(wert);

    //Errechnen der Realen Breite des Balkens in Pixel
    let reale_breite = percent * 5;

    let lc = document.getElementById("lc");
    //Zuweisen der realen Breite mittels CSS - width und dem Inline style Attribut
    lc.style.width = reale_breite + "px";

    //alert(wert);
    if (percent > 75) { 		//Grün
        lc.style.backgroundColor = "#009900";
    } else if (percent > 50 && percent < 76) {		//gelb
        lc.style.backgroundColor = "#ffff00";
    } else if (percent > 25 && percent < 51) {		//orange
        lc.style.backgroundColor = "#ff8000";
    } else if (percent < 26) {		//rot
        lc.style.backgroundColor = "#ff0000";
    }
}
/***********************************************************/


function damage(points) {
    player.damage(points)
}

function heal(points) {
    player.damage(-points)
}/*

function randomNumber(min, max) {
    return Math.random() * (max - min) + min;
}*/

function levelComplete() {
    complete = true;
    $('#menu_text').text('Level Complete');
    $('#menu').show();
}

function genLvl(lvl){
    genTerrain(lvl.terrain,lvl.flagX,lvl.flagY);
    player.setMaxLife(lvl.time);
}

function genTerrain(terrain,flagX,flagY) {
    for (let i = 0; i < terrain.length; i++) {
        new Stehdings(i).setPos(terrain[i].x,terrain[i].y)
    }
    new Flag(terrain.length).setPos(flagX,flagY)
}

//let verhaelltnis = {width: 3, height: 2};

function resize() {
    let elem = $('#game');
    //let minsize = Math.min(Number(elem.css('height').replace('px','')),Number(elem.css('width').replace('px','')));
    //size = (minsize/(((minsize===Number(elem.css('height').replace('px','')))?verhaelltnis.height:verhaelltnis.width)*50));
    ground = elem.height()-100;
    $('#ground').css({top: ground+'px'});
}

function nextLvl() {
    objects.forEach(value => {
        value.remove();
    });
    while (objects.length > 0) {
        objects.forEach(() => {
            objects.pop();
        });
    }
    $('#menu').hide();
    level++;
    genLvl(levels[level]);
    player.setPos(10,ground);
    player.setDead(false);
    complete = false;
    $('#objects>*:has(img[src="./flag.gif"])').css('z-index', 0);
    if (!(levels.length > level+1)) {
        $('#next').hide();
    }
}

function addLevelFromJSON(json) {
    addLevel(JSON.parse(json));
}

function addLevel(level) {
    if (level.terrain && level.flagX && level.flagY && level.time)
        levels.push(level);
}

function setup() {
    levels.push(new Level([
        {x:336, y:415}
    ],370,353, 200));

    levels.push(new Level([
        {x:136, y:415},
        {x:284, y:308},
        {x:185, y:184},
        {x:494, y:130},
        {x:710, y:119},
        {x:796, y:119}
    ],802,59, 350));

    //Events
    document.addEventListener("fullscreenchange", resize, false);
    document.addEventListener("webkitfullscreenchange", resize, false);
    document.addEventListener("mozfullscreenchange", resize, false);
    document.addEventListener("msfullscreenchange", resize, false);
    $(document).resize(resize);
    let next = $('#next');
    let restart = $('#restart');
    let start = $('#start');
    start.click(function () {
        $('#menu').hide();
        restart.show();
        start.hide();
        next.show();
        nextLvl();
        repeat();
    });
    next.click(nextLvl);
    restart.click(function () {
        player.setDead(false);
        complete = false;
        $('#menu').hide();
    });
    let elem = $(document.body);
    elem.keydown(KeyDown);
    elem.keyup(KeyUp);
    elem.keypress(KeyPressed);

    player = new Player('character',10,ground);
    resize();
    restart.hide();
    start.show();
    next.hide();
    $('#ground').css({top: ground+'px'});

    //Debug
    $('#check').click(function () {
        console.log(player.isJumping());
        console.log(player.collideDown());
    });
}
