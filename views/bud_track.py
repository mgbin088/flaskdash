from flask import current_app, Blueprint, jsonify, render_template, Response, current_app, abort
bud_track = Blueprint('bud_track', __name__)

from flask_security import login_required, current_user, roles_required

from mahercpa.modules.data_helpers import *

from mahercpa.modules.models import *
from mahercpa.modules.data_processing import *
from mahercpa.modules.data_collection import *
from mahercpa.modules.reports import *
from sqlalchemy.dialects.postgresql import aggregate_order_by
data = data_collection('/var/www/data/')
pd.set_option('display.max_colwidth', -1)

@bud_track.before_app_first_request
def get_data():
    #data.get_data()
    pass

##############################################################################
#
#BUDGET DASHBOARD
#############################################################################
@bud_track.route("/client/<client>/budget/<dept_id>")
@login_required
def budget(client=None, dept_id=None):
    ## SETUP CLIENT
    user = current_user
    if client is None:
        client = user.client[0].abbreviation
    else:
        client = Client.query.filter(Client.abbreviation.ilike(client)).first()
    
    if not current_user.has_role(client.abbreviation.lower()):
        abort(403)
        
    from mahercpa.modules.models_views import BudgetActual
        
    ##Get Data for Menu (budget departments)
    departments = []
    [departments.append({i.id : i.name}) 
     for i in (db.session.query(HeirarchyNode)
             .join(Client, HeirarchyVersion)
             .filter(Client.id==client.id, 
                     HeirarchyVersion.name == 'Budget', 
                     HeirarchyNode.parent_id==None)
             .order_by(HeirarchyNode.name))]
    
    sidebar = {}
    sidebar['client'] = client.abbreviation.lower()
    sidebar['departments'] = departments
    sidebar['fmonths'] = fyear_list(client=client).to_dict(orient='record')
    
    #get current budget department
    dept = (db.session.query(HeirarchyNode)
                    .join(Client, HeirarchyVersion)
                    .filter(Client.id==client.id, 
                         HeirarchyVersion.name == 'Budget', 
                         HeirarchyNode.id == dept_id)).first()
    
    #cdata = data.__dict__[client.abbreviation.lower()]
    rba = rpt_budget_dept(db = db)
    rbp = rpt_present(rba.get_budget_actual_bullet_charts(dept.id, client))
    blt = rbp.html()

    return render_template('budget_expense.html', budget_line_table = blt, sb=sidebar, dept=dept) 


@bud_track.route("/client/<client>/data/vendordetail/<dept_id>")
@login_required
def budget_deptx(client, dept_id):
    user = current_user
    if client is None:
        client = user.client[0].abbreviation
    else:
        client = Client.query.filter(Client.abbreviation.ilike(client)).first()
    
    if not current_user.has_role(client.abbreviation.lower()):
        abort(403)

    

    from mahercpa.modules.models_views import get_budget_actual, BudgetSpendJson, TransactionDetail, func, and_

    td = TransactionDetail
    dt_filt = (datetime(2017,4,1), datetime(2018,3,30))
    
    txn = (db.session.query(td.budget, td.vendor, td.period, td.amount)
                    .filter(td.client_id==client.id)
                    .filter(td.period.between(dt_filt[0],dt_filt[1]), td.path_id.any(dept_id))
                    .subquery())
    
    q1 = (db.session.query(txn.c.budget,txn.c.vendor,
                          func.json_object_agg(txn.c.period, txn.c.amount).label('months'))
                          .group_by(txn.c.budget,txn.c.vendor).subquery())
    q2 = (db.session.query(td.budget,td.vendor, 
                           func.json_agg(aggregate_order_by(
                               func.json_build_object('date',td.date,
                           'memo', td.memo,'id',td.id, 'txn_num',td.txn_number,
                           'ref_num', td.ref_num,'amount' ,td.amount),order_by=td.date))
                           .label('transactions'))
            .filter(td.client_id==client.id)
            .filter(td.period.between(dt_filt[0],dt_filt[1]), td.path_id.any(dept_id))
            .group_by(td.budget,td.vendor)).subquery()
    
    spend_obj = (db.session.query(q1.c.budget, q2.c.vendor, 
                func.json_build_object('budget',q1.c.budget, 'vendor', 
                q1.c.vendor,'totals',q1.c.months,'transactions',q2.c.transactions).label('json'))
                .join(q2, and_(q1.c.budget == q2.c.budget, q1.c.vendor == q2.c.vendor))
                .all())
                
    return jsonify([r.json for r in spend_obj])


@bud_track.route("/client/<client>/data/budget/<dept_id>")
def budget_dept(client, dept_id):
    if client is None:
        client = current_user.client[0].abbreviation
    else:
        client = Client.query.filter(Client.abbreviation.ilike(client)).first()
    
    if not current_user.has_role(client.abbreviation.lower()):
        abort(403)
    #print('running budget...')
    rdata = rpt_budget_dept(db) #data.__dict__[client.abbreviation.lower()],
    dept = (db.session.query(HeirarchyNode)
                .join(Client, HeirarchyVersion)
                .filter(Client.id == client.id, 
                     HeirarchyVersion.name == 'Budget', 
                     HeirarchyNode.id == dept_id)).first()
    
    #rep = rpt_present(rdata.get_budget_actual('Outreach and communications'))
    ba_cume = rpt_present(rdata.get_budget_actual_month_by_dept(dept.id, client=client, fyear=2018))
    spend_by_line = rpt_present(rdata.get_spend_by_line(dept.id, client, fyear=2018))
    
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
    user = current_user
    if client is None:
        client = user.client[0].abbreviation
    
    if not current_user.has_role(client):
        abort(403)
    
    cdata = data.__dict__[client.lower()]
    rba = rpt_budget_dept(cdata)
    #vendor_detail = rpt_present(rba.get_vendor_detail('Outreach and communications','wpONcall'))
    #vendor_tbl = rpt_present(
    #                rba.get_vendor_detail(dept.name,'wpONcall')
                    #rba.get_vendor_monthly_spend('Outreach and communications')
    #                ).df.to_json(orient='records')    #.datatables()
                    
    return  jsonify(rba.budget_spend_detail(dept.name)) #Response(vendor_tbl)