from flask import Flask, render_template, jsonify, send_file, url_for, redirect
from modules import datasources
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemySessionUserDatastore, \
    UserMixin, RoleMixin, login_required, utils

from modules.database import db_session, init_db
from modules.models import User, Role
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'

# After 'Create app'
#app.config['MAIL_SERVER'] = 'server2'
#app.config['MAIL_USERNAME'] = 'MAHER\ben'
#app.config['MAIL_PASSWORD'] = ''
#mail = Mail(app)

# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
security = Security(app, user_datastore)

# Create a user to test with
@app.before_first_request
def create_user():
    init_db()
#    user_datastore.create_user(email='ben@benjaminmaher.com', password='password')
#    db_session.commit()

# Views
@app.route('/')
@login_required
def home():
    return redirect(url_for('dash'))


@app.route("/jsondata")
def jsondata():
    return datasources.query_json()

@app.route("/usage_comparison")
def usage_comparison():
    return send_file('data/usage_comparison.csv',cache_timeout=60)

@app.route("/sample_json")
def sample_json():
    """ return json ajax """
    x = datasources.query_usage_table()
    return (jsonify(x))


@app.route("/logout")
def j2():
    utils.logout_user()
    return "logged out"


@app.route("/dash")
@login_required
def dash():
    file = open('data/usage_comparison.csv','r')
    usage_comparison = file.read()
    dt, col = datasources.query_usage_table()
    return render_template('dash_content_test.html', usage_comparison=usage_comparison, dt_data = (dt), dt_cols = (col))


@app.route("/morris")
def morris():
    return render_template('morris.html')


if __name__ == '__main__':
    app.run()
