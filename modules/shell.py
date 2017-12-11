from flask import Flask, render_template, jsonify, send_file, url_for, redirect
from modules import datasources
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin, login_required, utils, core

from modules.database import *
from modules.models import *
import pandas as pd

# At top of file
#from flask_mail import Mail

# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
#app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_PASSWORD_SALT'] = 'salty'
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False

app.config['SECURITY_POST_LOGIN_VIEW'] = '/dash'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/dash'
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'

# Setup Flask-Security
from flask_security.forms import RegisterForm, StringField, Required

user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
security = Security(app, user_datastore)

init_db()
