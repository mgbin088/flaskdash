from flask import Flask, render_template, jsonify, send_file, url_for, redirect, Response, abort, before_first_request
from mahercpa import app, mail, security, user_datastore
from .modules import datasources
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin, login_required, roles_required, roles_accepted, utils, core, current_user
from flask_security.forms import RegisterForm, StringField, Required
from flask_security.signals import user_registered

from .modules.database import *
from .modules.models import *
from .modules.data_processing import *
from .modules.data_collection import *
from .modules.reports import *

# Setup Flask-Security
import pandas as pd
import os
from datetime import datetime
###from flask_mail import Mail
pd.set_option('display.max_colwidth', -1)


# Create app
#app = Flask(__name__)
#app.config.from_envvar('FLASKDASH_SETTINGS')

#mail = Mail(app)

#Cache Client Data
@app.before_first_request
def run_first():
    data = data_collection(app.config['DATA_PATH'])
    data.get_data()

#class ExtendedRegisterForm(RegisterForm):
#    company = StringField('company', [Required()])

init_db()
###user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
###security = Security(app, user_datastore)
#security = Security(app, user_datastore, register_form=ExtendedRegisterForm)

@roles_required('admin')
@app.route('/init')
def populate_new_db():
    from flask_security.utils import encrypt_password
    #init_db()
    #user_client = db_session.query(Client).filter_by(abbreviation='MCE').first()
    #print(user_client.name)
    mce = Client(name='Marin Clean Energy', domain='mcecleanenergy.org',abbreviation='MCE')
    svce = Client(name='Silicon Valley Clean Energy', domain='svcleanenergy.org',abbreviation='SVCE')
    scp = Client(name='Sonoma Clean Power', domain='sonomacleanpower.org',abbreviation='SCP')
    pce = Client(name='Peninsula Clean Energy', domain='peninsulacleanenergy.com',abbreviation='PCE')
    #maher = Client(name='Maher Accountancy', domain='mahercpa.com',abbreviation='MAHER')
    for c in [mce,scp,pce,svce]:
        db_session.add(c)
    
    user_datastore.create_user(email='bmaher@mahercpa.com', password=encrypt_password('password'), confirmed_at=datetime(2017,1,1))
    user_datastore.create_user(email='ben@benjaminmaher.com', password=encrypt_password('password'), confirmed_at=datetime(2017,1,1))
    
    for r in ['admin','mce','scp','pce','svce']:
        user_datastore.create_role(name=r)

    db_session.commit()
    
    #Assing Default Roles
    for r in ['admin','mce','scp','pce','svce']:
        user_datastore.add_role_to_user(user_datastore.get_user('bmaher@mahercpa.com'), r)
    
    user_datastore.add_role_to_user(user_datastore.get_user('ben@benjaminmaher.com'), 'scp')
    
    #Assing Default Clients
    user = user_datastore.get_user('bmaher@mahercpa.com')
    for c in [mce,scp,pce,svce]:
        c.users.append(user)
    
    scp.users.append(user_datastore.get_user('ben@benjaminmaher.com'))
    
    
    db_session.commit()
    return Response('OK!')



# This processor is added to only the register view
@security.register_context_processor
def security_register_processor():
    return dict(company="company")


# Views
@app.route('/')
@login_required
def home():
    return redirect('/budget')


@app.route("/jsondata")
def jsondata():
    return datasources.query_json()

@app.route("/usage_comparison")
def usage_comparison():
    return send_file('data/usage_comparison.csv', cache_timeout=60)

@app.route("/sample_json")
def sample_json():
    """ return json ajax """
    x = datasources.query_usage_table()
    return (jsonify(x))


@app.route("/logout")
def logout():
    utils.logout_user()
    return "logged out"


@app.route("/dash")
def dash_redirect():
    user = user_datastore.get_user(current_user.email)
    if client is None:
        client = user.client[0].abbreviation
    
    if not current_user.has_role(client):
        abort(403)
    re_url = "/client/{}/dash".format(client.lower())
    return redirect((re_url))
    
@app.route("/budget")
@login_required
def budget_redirect():
    user = user_datastore.get_user(current_user.email)
    if user is not None:
        client = user.client[0].abbreviation
    
    if user is None:
        abort(403)
    
    re_url = "/client/{}/budget".format(client.lower())
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
    
    departments = []
    [departments.append({i.id : i.name}) 
     for i in (db_session.query(HeirarchyNode)
             .join(Client, HeirarchyVersion)
             .filter(Client.abbreviation.ilike(client), 
                     HeirarchyVersion.name == 'Budget', 
                     HeirarchyNode.parent_id==None)
             .order_by(HeirarchyNode.name))]
    
    sidebar = {}
    sidebar['client'] = client
    sidebar['departments'] = departments
    
    ##Prep Dashboard
    #file = open('data/usage_comparison.csv','r')
    #usage_comparison = file.read()
    dt, col = datasources.query_usage_table()
    invoice_matrix = invoice_usage_matrix('pce','usage_total_kwh', 20161101, 20171101) \
                        .to_html(classes = 'table table-hover table-small-row" id="tblUsageInvoice', border = 0, \
                        float_format=lambda x: '{:,.0f}'.format(x))
    role_list = [i.name for i in core.current_user.roles]        
    role_list = ','.join(role_list)
    print(role_list)
    return render_template('dash_content_test.html', \
        usage_comparison=usage_comparison, \
        dt_data = (dt), dt_cols = (col), client=client, role_names = role_list, invoice_matrix = invoice_matrix, sb=sidebar)

@app.route("/data/chartist")
def newchart():
    return jsonify(datasources.chartjs_data(data.scp, 'pce', nolabels=False))

@app.route("/chart")
def data_chartist():
    return render_template('chartjs.html')


##############################################################################
#
#BUDGET DASHBOARD
#############################################################################
@app.route("/client/<client>/budget/<dept_id>")
@login_required
def budget(client=None, dept_id=None):
    ## SETUP CLIENT
    user = user_datastore.get_user(current_user.email)
    if client is None:
        client = user.client[0].abbreviation
    
    if not current_user.has_role(client):
        abort(403)
        
    ##Get Data for Menu (budget departments)
    departments = []
    [departments.append({i.id : i.name}) 
     for i in (db_session.query(HeirarchyNode)
             .join(Client, HeirarchyVersion)
             .filter(Client.abbreviation.ilike(client), 
                     HeirarchyVersion.name == 'Budget', 
                     HeirarchyNode.parent_id==None)
             .order_by(HeirarchyNode.name))]
    
    sidebar = {}
    sidebar['client'] = client
    sidebar['departments'] = departments
    
    #get current budget department
    dept = (db_session.query(HeirarchyNode)
                    .join(Client, HeirarchyVersion)
                    .filter(Client.abbreviation.ilike(client), 
                         HeirarchyVersion.name == 'Budget', 
                         HeirarchyNode.id == dept_id)).first()
    
    cdata = data.__dict__[client.lower()]
    rba = rpt_budget_dept(cdata)
    rbp = rpt_present(rba.get_budget_actual_bullet_charts(dept.name))
    blt = rbp.html()
    vendor_detail = rpt_present(rba.get_vendor_detail(dept.name))
    
    print(vendor_detail.df.info())
    
    vendor_tbl = rpt_present(
                    rba.get_vendor_monthly_spend(dept.name)
                    ).html(html_id="vendors", escape=False,index =False)
                    
    return render_template('budget_expense.html', budget_line_table = blt, vendor_tbl = vendor_tbl, vendor_detail=vendor_detail.html(html_id="vendors",index =False), sb=sidebar, dept=dept)

@app.route("/client/<client>/data/vendordetail/<dept_id>")
@login_required
def get_vendor_json(client, dept_id):
    dept = (db_session.query(HeirarchyNode)
                .join(Client, HeirarchyVersion)
                .filter(Client.abbreviation.ilike(client), 
                     HeirarchyVersion.name == 'Budget', 
                     HeirarchyNode.id == dept_id)).first()

    ## SETUP CLIENT
    user = user_datastore.get_user(current_user.email)
    if client is None:
        client = user.client[0].abbreviation
    
    if not current_user.has_role(client):
        abort(403)
    
    cdata = data.__dict__[client.lower()]
    rba = rpt_budget_dept(cdata)
    #vendor_detail = rpt_present(rba.get_vendor_detail('Outreach and communications','wpONcall'))
    vendor_tbl = rpt_present(
                    rba.get_vendor_detail(dept.name,'wpONcall')
                    #rba.get_vendor_monthly_spend('Outreach and communications')
                    ).df.to_json(orient='records')    #.datatables()
                    
    return  jsonify(rba.budget_spend_detail(dept.name)) #Response(vendor_tbl)


@app.route("/budgeti/<int:dept>/<title>")
@login_required
#@app.route("/budget", methods=['GET'])
def budgeti(dept, title):
    import math
    
    
    cdata = data.__dict__['scp']
    rba = rpt_budget_dept(cdata)
    rbp = rpt_present(rba.get_budget_actual('Outreach and communications'))
    #target, performance, range1, range2, range3,
    ht = '<span class="sparkline" data-type="bullet" data-width="100%" data-height="100px" data-targetColor="#111" data-performanceColor="#42869e" data-rangeColors=["#C1AA7F","#C4AFDD","#60B66A"]>{}</span>'
    max_rng = math.ceil(rbp.df.loc[:,'Budget'].max()/10000)*10000
    
    d = rbp.df.assign(bullet = lambda df: df['Budget'].astype('int').astype('str') + ',' + df['Spent'].astype('int').astype('str') + ',' + str(max_rng))    #.map(lambda x: ns(x)))   #.astype('int').astype('str')))
    d['bullet'] = d['bullet'].map(lambda x: ht.format(x))
    #tbl = pd.DataFrame({'desc':["This",'That','Other'],'amount':[1,2,3],'html':['<b>bold</b>','br<br>ea<br>k','none']}).to_html(escape=False,index =False)
    return render_template('blank.html', content=d.to_html(escape=False,index =False))
    #return Response(tbl, mimetype='text/xml')
    
@app.route("/client/<client>/data/budget/<dept_id>")
def budget_dept(client, dept_id):

    #print('running budget...')
    rdata = rpt_budget_dept(data.__dict__[client.lower()])
    dept = (db_session.query(HeirarchyNode)
                .join(Client, HeirarchyVersion)
                .filter(Client.abbreviation.ilike(client), 
                     HeirarchyVersion.name == 'Budget', 
                     HeirarchyNode.id == dept_id)).first()
    
    #rep = rpt_present(rdata.get_budget_actual('Outreach and communications'))
    ba_cume = rpt_present(rdata.get_budget_actual_month_by_dept(dept.name))
    spend_by_line = rpt_present(rdata.get_spend_by_line(dept.name))
    
    #print(dept)
    #tbl = r.get_budget_actual(dept).to_html(float_format=lambda x: '{:,.0f}'.format(x), index=False)
    chart_data = {}
    #chart_data['norm'] = rep.chartjs_data(data_col_list = ['Budget','Spent'], cumulative=False) #data_col_list=['Spent','Remaining'], index_col_list='budget_line')
    chart_data['norm'] = spend_by_line.chartjs_data()
    chart_data['cume'] = ba_cume.chartjs_data(data_col_list = ['Budget','Spent'], cumulative=True, pallet_name='default')
    #return render_template('blank.html', content=tbl)
    return jsonify(chart_data) #Response(tbl, mimetype='text/xml')


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

@roles_required('admin')
@app.route('/client/<client>/makebudget')
def makebudget(client):
    
    if client is None:
        client = current_user.client[0].abbreviation
    
    if not current_user.has_role(client):
        abort(403)
    
    c = '{}:{}'.format(client, current_user.email)
    
    bv = BudgetVersion.query.filter_by(client_id=current_user.client[0].id)
    bvl = [b.name for b in bv]
    
    return render_template('makebudget.html', content=bvl[0])


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


#if __name__ == '__main__':
#    app.run(host='0.0.0.0')

