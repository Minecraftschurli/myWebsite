from flask_user import UserManager
from flask_user.forms import RegisterForm
from flask_user.translation_utils import lazy_gettext as _
from wtforms import StringField
from wtforms.validators import DataRequired


class CustomRegisterForm(RegisterForm):
    # Add a country field to the Register form
    first_name = StringField(_('First Name'), validators=[DataRequired()])
    last_name = StringField(_('Last Name'), validators=[DataRequired()])


# Customize Flask-User
class CustomUserManager(UserManager):

    def customize(self, app):
        # Configure customized forms
        self.RegisterFormClass = CustomRegisterForm
