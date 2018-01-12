#from flask import Flask, render_template, jsonify, send_file, url_for, redirect, Response
from flaskdash import *
from modules import datasources

from modules.database import *
from modules.models import *
from modules.data_processing import *
from modules.data_collection import *
import modules.reports as rpt
import pandas as pd
import os


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
    print(dt)
    print('i did')
    invoice_matrix = invoice_usage_matrix('pce','usage_total_kwh', 20161101, 20171101) \
                        .to_html(classes = 'table table-hover table-small-row" id="tblUsageInvoice', border = 0, \
                        float_format=lambda x: '{:,.0f}'.format(x))
    role_list = [i.name for i in core.current_user.roles]        
    role_list = ','.join(role_list)
    return render_template('dash_content_test.html', \
        usage_comparison=usage_comparison, \
        dt_data = (dt), dt_cols = (col), role_names = role_list, invoice_matrix = invoice_matrix)

@app.route("/data/chartist")
def newchart():
    return jsonify(datasources.chartjs_data(data.scp, 'pce', nolabels=False))

@app.route("/newchart")
def data_chartist():
    return render_template('chartjs.html')


@app.route("/budget/<dept>")
def budget(dept):
    r = rpt.rpt_budget_dept(data.scp)
    #print(dept)
    tbl = r.get_budget_actual(dept).to_html(float_format=lambda x: '{:,.0f}'.format(x), index=False)
    #return render_template('blank.html', content=tbl)
    return Response(tbl, mimetype='text/xml')


@app.route("/pdf/budget")
def budgetpdf():
    fname = 'mce_2017-10_budget_reports.pdf'
    return send_file(os.path.join(data_path, fname))
