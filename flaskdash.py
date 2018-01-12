from flask import Flask, render_template, jsonify, send_file, url_for, redirect, Response, abort
from modules import datasources
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin, login_required, roles_required, roles_accepted, utils, core, current_user
from flask_security.forms import RegisterForm, StringField, Required

from modules.database import *
from modules.models import *
from modules.data_processing import *
from modules.data_collection import *
import modules.reports as rpt

# Setup Flask-Security
import pandas as pd
import os
from flask_mail import Mail

# Create app
app = Flask(__name__)
app.config.from_envvar('FLASKDASH_SETTINGS')

mail = Mail(app)

#Cache Client Data
data = data_collection(app.config['DATA_PATH'])
data.get_data()


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
    #scp = Client(name='Sonoma Clean Power', domain='sonomacleanpower.org',abbreviation='SCP')
    pce = Client(name='Peninsula Clean Energy', domain='peninsulacleanenergy.com',abbreviation='PCE')
    #svce = Client(name='Silicon Valley Clean Energy', domain='svcleanenergy.org',abbreviation='SVCE')
    #maher = Client(name='Maher Accountancy', domain='mahercpa.com',abbreviation='MAHER')
    #db_session.add(svce)
    db_session.add(pce)
    #db_session.add(maher)
    #user_datastore.create_user(email='ben@benjaminmaher.com', password='password')
    db_session.commit()
#create_user()

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
def dash_redirect():
    user = user_datastore.get_user(current_user.email)
    client = user.client[0].abbreviation
    re_url = "/client/{}/dash".format(client.lower())
    return redirect((re_url))


@app.route("/client/<client>/dash")
@login_required
def dash(client=None):
    ## SETUP CLIENT
    print(client)
    user = user_datastore.get_user(current_user.email)
    if client is None:
        client = user.client[0].abbreviation
    
    if not current_user.has_role(client):
        abort(403)
    
    cdata = data.__dict__[client.lower()]
    
    ##Prep Dashboard
    file = open('data/usage_comparison.csv','r')
    usage_comparison = file.read()
    dt, col = datasources.query_usage_table()
    invoice_matrix = invoice_usage_matrix('pce','usage_total_kwh', 20161101, 20171101) \
                        .to_html(classes = 'table table-hover table-small-row" id="tblUsageInvoice', border = 0, \
                        float_format=lambda x: '{:,.0f}'.format(x))
    role_list = [i.name for i in core.current_user.roles]        
    role_list = ','.join(role_list)
    print(role_list)
    return render_template('dash_content_test.html', \
        usage_comparison=usage_comparison, \
        dt_data = (dt), dt_cols = (col), client=client, role_names = role_list, invoice_matrix = invoice_matrix)

@app.route("/data/chartist")
def newchart():
    return jsonify(datasources.chartjs_data(data.scp, 'pce', nolabels=False))

@app.route("/newchart")
def data_chartist():
        
    user = current_user
    user_domain = str(user.email).split('@')[1]
    print(user_domain)
    user_client = db_session.query(Client).filter_by(domain=user_domain).first()
    print(user_client.name)
    
    if user_client is not None:
        print(user_client.name)
        user_client.users.append(user)
        db_session.commit()
    return render_template('chartjs.html')


@app.route("/budget/<int:dept>/<title>")
@login_required
#@app.route("/budget", methods=['GET'])
def budget(dept, title):
    r = rpt.rpt_budget_dept(data.scp)
    print(title)
    d = data.scp.account_map.budget_department.unique()[dept]
    tbl = r.get_budget_actual(d).to_html(float_format=lambda x: '{:,.0f}'.format(x), index=False)
    return render_template('blank.html', content=tbl)
    #return Response(tbl, mimetype='text/xml')

@app.route('/tabletest')
def tabletest():
    r = rpt.rpt_budget_dept(data.scp)
    d = data.scp.account_map.budget_department.unique()[1]
    tbl = r.get_budget_actual(d).to_html(float_format=lambda x: '{:,.0f}'.format(x), index=False)
    return render_template('tabletest.html', content=tbl)
    

@app.route("/pdf/budget")
def budgetpdf():
    fname = 'mce_2017-10_budget_reports.pdf'
    return send_file(os.path.join(data_path, fname))

@app.route("/users/delete/<user_name>")
@login_required
@roles_required('admin')
def delete_user(user_name):
    user = user_datastore.get_user(user_name)
    user_datastore.delete_user(user)
    db_session.commit()
    return Response(user_name)

@app.route("/roles/create/<role_name>")
@login_required
@roles_required('admin')
def add_role(role_name):
    user_datastore.create_role(name=role_name)
    db_session.commit()
    return Response(role_name)

@app.route("/client/assign/<client>/<user_name>")
@login_required
@roles_required('admin')
def add_user_to_client(client, user_name):
    client = db_session.query(Client).filter_by(abbreviation=client.upper()).first()
    user = user_datastore.get_user(user_name)
    print(client.name)
    print(user.email)
    if client is not None and user is not None:
        print(client.name, user.email)
        client.users.append(user)
        db_session.commit()
    return Response(user.email)

@app.route("/me")
@login_required
def whoami():
    user = user_datastore.get_user(current_user.email)
    client_list = "client(s): " + ','.join([i.domain for i in user.client])
    role_list = "roles(s): " + ','.join([i.name for i in user.roles])
    return Response(user.email + ": " + client_list + "; " + role_list)

    
@app.route("/client/<client_abbrev>/old")
@login_required
def show_client_data(client_abbrev):
    user = user_datastore.get_user(current_user.email)
    if not current_user.has_role(client_abbrev):
        abort(403)
    
    client = client_abbrev
    cdata = data.__dict__[client]
    
    #print(type(current_user.clients))
    #client_list = "client(s): " + ','.join([i.domain for i in user.client])
    #role_list = "roles(s): " + ','.join([i.name for i in user.roles])
    #return render_template('blank.html', content=cdata.table_statistics.to_html())
    return redirect()
    
    
    
    

@app.route("/roles/assign/<user>/<role>")
@login_required
@roles_required('admin')
def add_role_to_user(user, role):
    print(user, role)
    user_datastore.add_role_to_user(user, role)
    db_session.commit()
    return Response(role)

    
from flask_security.signals import user_registered

@user_registered.connect_via(app)
def user_registered_sighandler(sender, user, confirm_token):
    #print("print-user_registered_sighandler:", user.email)
    user_domain = str(user.email).split('@')[1]
    #print(user_domain)
    user_client = db_session.query(Client).filter_by(domain=user_domain).first()

    if user_client is not None:
        print(user_client.name)
        user_client.users.append(user)
        db_session.commit()
        


user_registered.connect(user_registered_sighandler)


if __name__ == '__main__':
    app.run(host='0.0.0.0')

