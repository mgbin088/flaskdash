from flask import current_app, Blueprint, jsonify, render_template, Response, current_app
bud_track = Blueprint('bud_track', __name__)

from flask_security import login_required, current_user, roles_required

from mahercpa.modules.models import *
from mahercpa.modules.data_processing import *
from mahercpa.modules.data_collection import *
from mahercpa.modules.reports import *

data = data_collection('/var/www/data/')
pd.set_option('display.max_colwidth', -1)

@bud_track.before_app_first_request
def get_data():
    data.get_data()

##############################################################################
#
#BUDGET DASHBOARD
#############################################################################
@bud_track.route("/client/<client>/budget/<dept_id>")
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
     for i in (db.session.query(HeirarchyNode)
             .join(Client, HeirarchyVersion)
             .filter(Client.abbreviation.ilike(client), 
                     HeirarchyVersion.name == 'Budget', 
                     HeirarchyNode.parent_id==None)
             .order_by(HeirarchyNode.name))]
    
    sidebar = {}
    sidebar['client'] = client
    sidebar['departments'] = departments
    
    #get current budget department
    dept = (db.session.query(HeirarchyNode)
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


@bud_track.route("/client/<client>/data/budget/<dept_id>")
def budget_dept(client, dept_id):

    #print('running budget...')
    rdata = rpt_budget_dept(data.__dict__[client.lower()])
    dept = (db.session.query(HeirarchyNode)
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


@bud_track.route("/client/<client>/data/vendordetail/<dept_id>")
@login_required
def get_vendor_json(client, dept_id):
    dept = (db.session.query(HeirarchyNode)
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