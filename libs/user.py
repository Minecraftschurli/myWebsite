import json


class User:
    def __init__(self, firstname, lastname, username, password, email, permissions=None):
        self.lastname = lastname
        self.firstname = firstname
        if permissions is None:
            permissions = list()
        self.username = username
        self.permissions = permissions
        self.password = password
        self.email = email

    def to_dict(self):
        return {
            "firstname": self.firstname,
            "lastname": self.lastname,
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "permissions": self.permissions
        }

    def __str__(self):
        return json.dumps(dict(self.to_dict()))
