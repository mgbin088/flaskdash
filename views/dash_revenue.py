from flask import current_app, Blueprint, jsonify, render_template, Response, current_app
dash_revenue = Blueprint('dash_revenue', __name__)

from flask_security import login_required, current_user, roles_required

from mahercpa.modules.models import *
from mahercpa.modules.data_processing import *
from mahercpa.modules.data_collection import *
from mahercpa.modules.reports import *
from mahercpa.modules import datasources



data = data_collection('/var/www/data/')

@dash_revenue.before_app_first_request
def get_data():
    data.get_data()

@dash_revenue.route("/client/<client>/dash")
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
     for i in (db.session.query(HeirarchyNode)
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
    usage_comparison = data.__dict__[client.lower()].usage_comparison
    dt, col = datasources.query_usage_table()
    invoice_matrix = invoice_usage_matrix('pce','usage_total_kwh', 20161101, 20171101) \
                        .to_html(classes = 'table table-hover table-small-row" id="tblUsageInvoice', border = 0, \
                        float_format=lambda x: '{:,.0f}'.format(x))
    role_list = [i.name for i in current_user.roles]        
    role_list = ','.join(role_list)
    print(role_list)
    return render_template('dash_content_test.html', \
        usage_comparison=usage_comparison, \
        dt_data = (dt), dt_cols = (col), client=client, role_names = role_list, invoice_matrix = invoice_matrix, sb=sidebar)

@dash_revenue.route("/data/chartist")
def newchart():
    return jsonify(datasources.chartjs_data(data.scp, 'pce', nolabels=False))