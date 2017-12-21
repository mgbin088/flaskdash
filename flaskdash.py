from flask import Flask, render_template, jsonify, send_file, url_for, redirect
from modules import datasources
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin, login_required, utils, core
from modules.database import *
from modules.models import *
from modules.data_processing import *
import pandas as pd
import os
from flask_mail import Mail

# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['SECURITY_CONFIRMABLE'] = True
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_PASSWORD_SALT'] = 'salty'
app.config['SECURITY_SEND_REGISTER_EMAIL'] = True

app.config['SECURITY_POST_LOGIN_VIEW'] = '/dash'
app.config['SECURITY_POST_REGISTER_VIEW'] = '/dash'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user.db'

# After 'Create app'
app.config['MAIL_SERVER'] = 'mail.smtp2go.com'
app.config['SECURITY_EMAIL_SENDER'] = 'portal@mahercpa.com'
app.config['MAIL_PORT'] = '2525'
mail = Mail(app)

# Setup Flask-Security
from flask_security.forms import RegisterForm, StringField, Required

#class ExtendedRegisterForm(RegisterForm):
#    company = StringField('company', [Required()])

user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
security = Security(app, user_datastore)

#security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

# This processor is added to only the register view
@security.register_context_processor
def security_register_processor():
    return dict(company="company")

#Create a user to test with
#@app.before_first_request
def create_user():
    init_db()
    mce = Client(name='Marin Clean Energy', domain='mcecleanenergy.org',abbreviation='MCE')
    svce = Client(name='Silicon Valley Clean Energy', domain='svcleanenergy.org',abbreviation='SVCE')
    maher = Client(name='Maher Accountancy', domain='mahercpa.com',abbreviation='MAHER')
    db_session.add(svce)
    db_session.add(mce)
    db_session.add(maher)
    user_datastore.create_user(email='ben@benjaminmaher.com', password='password')
    #db_session.commit()


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
    invoice_matrix = invoice_usage_matrix('pce','usage_total_kwh', 20161101, 20171101) \
                        .to_html(classes = 'table table-hover table-small-row" id="tblUsageInvoice', border = 0, \
                        float_format=lambda x: '%12.1f' % x)
    role_list = [i.name for i in core.current_user.roles]        
    role_list = ','.join(role_list)
    return render_template('dash_content_test.html', \
        usage_comparison=usage_comparison, \
        dt_data = (dt), dt_cols = (col), role_names = role_list, invoice_matrix = invoice_matrix)

@app.route("/data/chartist")
def newchart():
    return jsonify(datasources.chartist_data('pce', nolabels=True))

@app.route("/newchart")
def data_chartist():
    return render_template('chartjs.html')


@app.route("/budget")
def budget():
    return render_template('budget_reports.html')

@app.route("/pdf/budget")
def budgetpdf():
    fname = 'mce_2017-10_budget_reports.pdf'
    return send_file(os.path.join(data_path, fname))


from flask_security.signals import user_registered

@user_registered.connect_via(app)
def user_registered_sighandler(sender, user, confirm_token):
    print("print-user_registered_sighandler:", user.email)
    user_domain = str(user.email).split('@')[1]
    print(user_domain)
    user_client = db_session.query(Client).filter_by(domain=user_domain).first()

    if user_client is not None:
        print(user_client.name)
        user_client.users.append(user)
        db_session.commit()


user_registered.connect(user_registered_sighandler)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

