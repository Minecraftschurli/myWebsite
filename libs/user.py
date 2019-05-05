import json

from flask_login import UserMixin


class User(UserMixin):
    def __init__(self,
                 first_name: str,
                 last_name: str,
                 username: str,
                 password_hash: str,
                 email: str,
                 permissions: list = None):

        if permissions is None:
            permissions = list()

        self.last_name = last_name
        self.first_name = first_name
        self.username = username
        self.permissions = permissions
        self.password_hash = password_hash
        self.email = email
        self.id = username

    def authenticate(self, password):
        from app import bcrypt
        return bcrypt.check_password_hash(self.password_hash.encode('utf-8'), password)

    @staticmethod
    def from_dict(user_dict: dict):
        user = User(
            user_dict['first_name'],
            user_dict['last_name'],
            user_dict['username'],
            user_dict['password_hash'],
            user_dict['email'],
            user_dict['permissions'])
        return user

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "password_hash": self.password_hash,
            "email": self.email,
            "permissions": self.permissions
        }

    def __str__(self):
        return json.dumps(dict(self.to_dict()))

    @property
    def __dict__(self):
        return self.to_dict()

    def has_permission(self, permission):
        if "all" in self.permissions:
            return True
        if isinstance(permission, tuple):
            for p in permission:
                if p in self.permissions:
                    return True
        else:
            return permission in self.permissions
        return False
