from flask import current_app, Blueprint, render_template, Response, current_app
main = Blueprint('main', __name__)


from flask import Flask, render_template, jsonify, send_file, url_for, redirect, Response, abort
#from mahercpa import app, mail, security, user_datastore
from mahercpa.modules import datasources
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin, login_required, roles_required, roles_accepted, utils, core, current_user
from flask_security.forms import RegisterForm, StringField, Required
from flask_security.signals import user_registered

#from mahercpa.modules.database import *
from mahercpa.modules.models import *
from mahercpa.modules.data_processing import *
from mahercpa.modules.data_collection import *
from mahercpa.modules.reports import *

# Setup Flask-Security
import pandas as pd
import os
from datetime import datetime

# Views
@main.route('/')
@login_required
def home():
    return redirect('/budget')


@main.route("/jsondata")
def jsondata():
    return datasources.query_json()

@main.route("/usage_comparison")
def usage_comparison():
    return send_file('data/usage_comparison.csv', cache_timeout=60)

@main.route("/sample_json")
def sample_json():
    """ return json ajax """
    x = datasources.query_usage_table()
    return (jsonify(x))


@main.route("/logout")
def logout():
    utils.logout_user()
    return "logged out"


@main.route("/dash")
def dash_redirect():
    client = current_user.client[0].abbreviation
    print(client)
    
    if not current_user.has_role(client):
        abort(403)
    re_url = "/client/{}/dash".format(client.lower())
    return redirect((re_url))
    
@main.route("/budget")
@login_required
def budget_redirect():
    user = user_datastore.get_user(current_user.email)
    if user is not None:
        client = user.client[0].abbreviation
    
    if user is None:
        abort(403)
    
    bud_id = {'scp':115,'mce':248}
    
    re_url = "/client/{}/budget/{}".format(client.lower(),bud_id[client.lower()])
    return redirect((re_url))




@main.route("/chart")
def data_chartist():
    return render_template('chartjs.html')



@main.route("/budgeti/<int:dept>/<title>")
@login_required
#@main.route("/budget", methods=['GET'])
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
    

@main.route('/tabletest')
def tabletest():
    r = rpt.rpt_budget_dept(data.scp)
    d = data.scp.account_map.budget_department.unique()[1]
    tbl = r.get_budget_actual(d).to_html(float_format=lambda x: '{:,.0f}'.format(x), index=False)
    return render_template('tabletest.html', content=tbl)
    

@main.route("/pdf/budget")
def budgetpdf():
    fname = 'mce_2017-10_budget_reports.pdf'
    return send_file(os.path.join(data_path, fname))

    


@roles_required('admin')
@main.route('/client/<client>/makebudget')
def makebudget(client):
    
    if client is None:
        client = current_user.client[0].abbreviation
    
    if not current_user.has_role(client):
        abort(403)
    
    c = '{}:{}'.format(client, current_user.email)
    
    bv = BudgetVersion.query.filter_by(client_id=current_user.client[0].id)
    bvl = [b.name for b in bv]
    
    return render_template('makebudget.html', content=bvl[0])





#if __name__ == '__main__':
#    app.run(host='0.0.0.0')

