from flask_login import UserMixin

from . import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    username = db.Column(db.String(100), primary_key=True)  # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True, nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    permissions = db.Column(db.String(1000), nullable=False)
    password_hash = db.Column(db.String(1000), nullable=False)

    def get_id(self):
        return self.username

    def has_permission(self, permission):
        if permission is "any":
            return True
        permissions = self.permissions.split(', ')
        if "all" in permissions:
            return True
        if isinstance(permission, list):
            for p in permission:
                if p in permissions:
                    return True
        else:
            return permission in permissions
        return False

    def authenticate(self, password):
        return bcrypt.check_password_hash(self.password_hash.encode('utf-8'), password)

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "password_hash": self.password_hash,
            "email": self.email,
            "permissions": self.permissions
        }


class IPBlacklist(db.Model):
    __tablename__ = 'ip_blacklist'

    ip = db.Column(db.String(15), primary_key=True, nullable=False)


class Contact(db.Model):
    __tablename__ = 'contact'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text(), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)


class ShootItData:
    class PerUser(db.Model):
        __tablename__ = 'shoot_it_data'

        username = db.Column(db.String(100), primary_key=True)
        score_easy = db.Column(db.Integer(), nullable=False)
        score_medium = db.Column(db.Integer(), nullable=False)
        score_hard = db.Column(db.Integer(), nullable=False)
        score_impossible = db.Column(db.Integer(), nullable=False)
        linked = db.Column(db.Boolean(), nullable=False)

        def __getitem__(self, item):
            return {
                'username': self.username,
                'easy': self.score_easy,
                'medium': self.score_medium,
                'hard': self.score_hard,
                'impossible': self.score_impossible,
                'linked': self.linked
            }.get(item.lower(), None)

    @staticmethod
    def get_data_for_user(user):
        user = ShootItData.PerUser.query.filter_by(username=user).first()
        if user:
            return user
        return None

    @staticmethod
    def get_anonymus_user(user):
        user = ShootItData.PerUser.query.filter_by(username=user).first()
        if user:
            return user
        return None

    @staticmethod
    def user_exists(user):
        user = ShootItData.PerUser.query.filter_by(username=user).first()
        if user:
            return True
        return False

    @staticmethod
    def create_and_get_user(user, **kwargs):
        link = 'assoc' in kwargs and kwargs['assoc'] is not None
        if link:
            user = kwargs['assoc']
        elif user is None:
            return None
        new_user = ShootItData.PerUser(username=user, score_easy=0, score_medium=0, score_hard=0, score_impossible=0,
                                       linked=link)
        db.session.add(new_user)
        db.session.commit()
        return ShootItData.get_anonymus_user(user)

    @staticmethod
    def get_highscores(difficulty, length=10):
        out = []
        dat = ShootItData.PerUser.query.filter(ShootItData.PerUser.username.isnot('dummy')).order_by(
            ShootItData.PerUser.username).limit(length).all()
        for x in dat:
            out.append((x.username, x[difficulty]))
        return out

    @staticmethod
    def update(username, difficulty, score):
        user = ShootItData.PerUser.query.get(username)
        if user:
            user[difficulty] = score
