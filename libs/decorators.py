import functools

from flask import abort
from flask_login import login_required

from . import login_manager
from .functions import check_permission, _check_ip


def permission_required(permission='any'):
    def decorator(func):
        if permission is not 'any':
            func = login_required(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if (permission is 'login' or permission is 'any') or check_permission(permission):
                return func(*args, **kwargs)
            else:
                return login_manager.unauthorized()

        return wrapper

    return decorator


def check_ip(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if _check_ip():
            return func(*args, **kwargs)
        else:
            abort(423)

    return wrapper
