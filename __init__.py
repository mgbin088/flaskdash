from flask import Flask, render_template, jsonify, send_file, url_for, redirect, Response
#from mahercpa.modules import datasources
#from flask_sqlalchemy import SQLAlchemy
#from flask_security import Security, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin, login_required, utils, core
#from flask_security.forms import RegisterForm, StringField, Required

#from mahercpa.modules.database import *
#from mahercpa.modules.models import *
#from modules.data_processing import *
#from modules.data_collection import *
#import modules.reports as rpt

# Setup Flask-Security
import pandas as pd
import os
from flask_mail import Mail

# Create app
app = Flask(__name__)
app.config.from_envvar('FLASKDASH_SETTINGS')

mail = Mail(app)

#Cache Client Data
#data = data_collection(app.config['DATA_PATH'])
#data.get_data()

#class ExtendedRegisterForm(RegisterForm):
#    company = StringField('company', [Required()])

#user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
#security = Security(app, user_datastore)

#Create a user to test with
#@app.before_first_request




from . import views

#if __name__ == '__main__':
#    app.run(host='0.0.0.0')

