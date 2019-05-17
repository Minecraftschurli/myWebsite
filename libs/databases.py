from flask_user import UserMixin

from . import db


# Define the User data-model.
# NB: Make sure to add flask_user UserMixin !!!
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default='')

    # User information
    username = db.Column(db.String(100), nullable=False, unique=True)
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    # Define the relationship to Role via UserRoles
    roles = db.relationship('Role', secondary='user_roles')

    def has_role(self, permission):
        roles = self.get_roles()
        if permission is "any":
            return True
        if "admin" in roles:
            return True
        if isinstance(permission, list):
            for p in permission:
                if p in roles:
                    return True
        else:
            return permission in roles
        return False

    def get_roles(self):
        from . import get_user_manager
        return get_user_manager().db_manager.get_user_roles(self)

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "password": self.password,
            "email": self.email
        }


# Define the Role data-model
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


# Define the UserRoles association table
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


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
