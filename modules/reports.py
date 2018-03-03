#import modules.data_collection as dc
import pandas as pd
import numpy as np
import math
pd.set_option('display.float_format', lambda x: '%.1f' % x)


class rpt_budget_dept:
    def __init__(self, db=None, data_col=None):
        self.db = db
        if data_col:
            self.data_col = data_col
        
            self.actual_orig = data_col.gl_transaction_detail
            self.account_map = data_col.account_map
            self.actual = self.actual_orig.merge(self.account_map, on='account_id',how='left')
        
            #Assign actuals table, fix dates
            #actual = data.scp.gl_transaction_detail.merge(data.scp.account_map, on='account_id',how='left')
            self.actual.date = self.actual['date'].astype('datetime64[D]')
            self.actual.set_index('date')
    
            #Assign budget table, fix dates
            self.budget = data_col.budget
            self.budget.date = pd.to_datetime(self.budget['date'],format='%m/%d/%Y')
    
            #Auto filter on YTD, may need to parameterize this further for Programs on Calendar Year
            dt_filt = "date >= '{}' & date <= '{}'".format(data_col.dates.ytd[0].strftime('%Y-%m-%d'), data_col.dates.ytd[1].strftime('%Y-%m-%d'))
            dt_filt_from = "date >= '{}'".format(data_col.dates.ytd[0].strftime('%Y-%m-%d'))
            dt_filt_to = "date <= '{}'".format(data_col.dates.ytd[1].strftime('%Y-%m-%d'))
    
            #Filter Actuals YTD and summarize by budgetline
            actual = (self.actual.copy().query(dt_filt_from)
                       .groupby(['budget_type','budget_department','budget_line','date']) #, 'account_name_x'
                       .agg({'amount':sum})
                       .rename(columns = {'amount':'Spent'})
            )

            #Filter Budget YTD and summarize by budgetline
            self.budget = (self.budget.query(dt_filt_from)
                       .groupby(['budget_type','budget_department','budget_line','date']) 
                       .agg({'budget_amount':sum})
                       .rename(columns = {'budget_amount':'Budget'})
            )
    
            self.budget_actual = (self.budget.join(actual, how='outer')).reset_index()  #.replace(0,'')
            self.budget_actual['date'] = pd.DatetimeIndex(self.budget_actual['date']).to_period('M')
            self.budget_actual = (self.budget_actual
                                    .groupby(['budget_type','budget_department','budget_line','date']) #, 'account_name_x'
                                    .agg(sum))
        
    def _qry_budget_actual(self, node_id, fiscal_year=None, client=None):
        from mahercpa.modules.models_views import BudgetActual, Calendar
        '''Get budget actual query, filtered by node (with all children) and filtered by fiscal year'''
        if not client and not fyear_start_mo:
            print("need fiscal year start or client")

        if not fiscal_year:
            fiscal_year = 2018

        fyear_start_mo = client.fyear_start_mo

        q = self.db.session.query(BudgetActual.path_name, BudgetActual.period, BudgetActual.actual, BudgetActual.budget).join(Calendar, BudgetActual.period==Calendar.date_actual)
        q = q.filter(BudgetActual.path_id.any(node_id))
        q = q.filter(BudgetActual.client_id==client.id, Calendar.__dict__['fiscal_year_{}'.format(str(fyear_start_mo))] == fiscal_year)
        s = q.statement.compile(self.db.engine)
        return pd.read_sql(s, self.db.engine)
    
    def get_budget_actual(self, budget_dept, client):
        #Test Budget Dept for Filter
        ba = self._qry_budget_actual(node_id=budget_dept, client=client)
        ba['budget_line'] = ba.loc[:,'path_name'].apply(lambda x: x[-1])
        rpt = (ba
             .rename(columns = {'actual':'Spent','budget':'Budget'})
             .drop(['path_name'],1)
             .groupby('budget_line')
             .agg(sum)
             .assign(Remaining = lambda df: (df['Budget'] - df['Spent']).clip(0,None))
             .assign(Over = lambda df: (df['Spent'] - df['Budget']).clip(0, None))
             .assign(spent_under = lambda df: df.loc[:, ['Spent', 'Budget']].min(axis=1))
              ).reset_index().fillna(0)
        #.pivot_table(index = ['budget_department','budget_line'],columns='date')
        return rpt 
        
    def get_budget_actual_bullet_charts(self, budget_dept, client):
        d = self.get_budget_actual(budget_dept, client=client).copy()
        #target, performance, range1, range2, range3,
        ht = '<span class="spark-bullet">{}</span>'
        max_rng = np.ceil(d.loc[:,'Budget'].max()/10000)*10000
        
        
        #conversion helper
        intstr = lambda df: df.astype('int').astype('str')
        #Merge columns into one comma delimited string
        d = d.assign(chart = lambda df: 
                          intstr(df['Budget']) + ',' + 
                          intstr(df['spent_under']) + ',' + 
                          str(max_rng) + ',' + 
                          intstr(df['Spent']) + ',' + 
                          intstr(df['spent_under']))
                          

        #Wrap in Span Tags for sparklines
        d['chart'] = d['chart'].map(lambda x: ht.format(x))
        d = d[['budget_line','Budget','chart','Spent','Remaining']]
        #Add Grand Total Row
        d = d.append(d.sum(numeric_only=True), ignore_index=True).fillna("")
        d.iloc[-1,d.columns.get_loc('budget_line')] = 'Total'
        return d
        
    def get_spend_by_line(self, dept, client, fyear=None, include_date=None):
        from mahercpa.modules.models_views import BudgetActual, Calendar
        '''Get budget actual query, filtered by node (with all children) and filtered by fiscal year'''
        fiscal_year = fyear
        fyear_start_mo = client.fyear_start_mo

        q = self.db.session.query(BudgetActual.name.label('budget_line'), BudgetActual.period.label('date'), BudgetActual.actual.label('Spent')).join(Calendar, BudgetActual.period==Calendar.date_actual)
        q = q.filter(BudgetActual.path_id.any(dept))
        q = q.filter(BudgetActual.client_id==client.id, Calendar.__dict__['fiscal_year_{}'.format(str(fyear_start_mo))] == fiscal_year)
        s = q.statement.compile(self.db.engine)
        #d = self.budget_actual.copy()
        d = pd.read_sql(s, self.db.engine)
        
        grp = ['budget_line','date']
        d = (d  #.query(dep_filt)
                 .reset_index()
                 .loc[:, grp + ['Spent']]
                 .groupby(grp)
                 .agg(sum)).pivot_table(values='Spent', columns='budget_line', index = 'date').fillna('')
        
        #d.index = pd.to_datetime(d.index,unit='D')
        return d
        
    def get_budget_actual_month_by_dept(self, dept, fyear, client, include_line=False):
        ##d = self.budget_actual.copy()
        ##dep_filt = 'budget_department == "{}"'.format(dept)
        from mahercpa.modules.models_views import BudgetActual, Calendar
        fiscal_year = fyear
        fyear_start_mo = client.fyear_start_mo

        q = self.db.session.query(BudgetActual.name.label('budget_line'), BudgetActual.period.label('date'), BudgetActual.actual.label('Spent'), BudgetActual.budget.label('Budget')).join(Calendar, BudgetActual.period==Calendar.date_actual)
        q = q.filter(BudgetActual.path_id.any(dept))
        q = q.filter(BudgetActual.client_id==client.id, Calendar.__dict__['fiscal_year_{}'.format(str(fyear_start_mo))] == fiscal_year)
        s = q.statement.compile(self.db.engine)
        #d = self.budget_actual.copy()
        d = pd.read_sql(s, self.db.engine)
        
        
        if include_line:
            grp = ['date','budget_line']
        else:
            grp = ['date']
        
        
        d = (d #.query(dep_filt)
                 #.reset_index()
                 .groupby(grp)
                 .agg(sum))
            
        if include_line:
            d = d.pivot_table(values)
        return d
        
    def get_vendor_monthly_spend(self, budget_dept, client):
        #budget_dept = 'Outreach and communications'
        filt_cat = "budget_department == '{}'".format(budget_dept)
        dt_filt = "date >= '{}' & date <= '{}'".format(self.data_col.dates.ytd[0].strftime('%Y-%m-%d'), self.data_col.dates.ytd[1].strftime('%Y-%m-%d'))

        vs = (self.actual
                 .query(dt_filt + " & " + filt_cat)
                 .groupby(['budget_line','name','month'])
                 .agg({'amount':sum})).pivot_table(values='amount', columns='month', index = ['budget_line', 'name']).fillna('')


        vs.columns = [pd.to_datetime(vs.columns).strftime("%b'%y")]
        vs.columns = vs.columns.get_level_values(0)
        vs = vs.reset_index()
        return vs
        
    def get_vendor_detail(self, budget_dept, vendor=''):
        #budget_dept = 'Outreach and communications'
        filt_cat = "budget_department == '{}'".format(budget_dept)
        dt_filt = "date >= '{}' & date <= '{}'".format(self.data_col.dates.ytd[0].strftime('%Y-%m-%d'), self.data_col.dates.ytd[1].strftime('%Y-%m-%d'))
        if vendor != '':
            filt_cat = filt_cat + " & name == '{}'".format(vendor)
            
        vs = (self.actual
                 .query(dt_filt + " & " + filt_cat)
                 .loc[:,['txn_number','date','ref_num','name','line_memo','amount']]
             )
        return vs
        
    def budget_spend_detail(self, budget_dept):    
        
        #Get Vendor Summary Data and Group by Budget Line
        vendor_summary = (self.get_vendor_monthly_spend(budget_dept)
                            .groupby('budget_line'))
    
        #Get Vendor Transaction Data and Group by Vendor
        vendor_txns = (self.get_vendor_detail(budget_dept).fillna('')
                       .groupby('name'))
    
        #Create Dict object nested by Vendor Name
        txn = {}
        for index, value in vendor_txns:
            txn[index] = value.to_dict(orient='record')
    
        #Create Parent object and merge in transaction detail {Budget_line -> Vendor -> Transactions}
        spend = []
        for bud_line, line_df in vendor_summary:
            vendor_df = line_df.to_dict(orient='record')
            for vendor_line in vendor_df:    
                #print(vendor_txns[vendor_line['name']])
                vendor_line['transactions'] = txn[vendor_line['name']]
            spend.append(vendor_df)
        #Flatten List on Return
        flatten = [item for items in spend for item in items]
        return flatten
        
        
        
        
class rpt_present:
    def __init__(self, dataframe):
        self.df = dataframe
        self.pallet = {'default':['rgba(60, 122, 146, .2)','rgba(60, 122, 146, .7)','rgba(212, 0, 0, .8)','rgba(212, 219, 206, 1)','rgba(78, 152, 143, 1)'],
                       'default-7':['rgba(60, 122, 146, .2)','rgba(60, 122, 146, .7)','rgba(212, 0, 0, .8)','rgba(212, 219, 206, 1)','rgba(78, 152, 143, 1)'],
                       'categorical': ["rgba(51, 110, 147, 1)", "rgba(38, 168, 73, 1)", "rgba(99, 99, 97, 1)", "rgba(198, 85, 85, 1)", "rgba(198, 161, 85, 1)", "rgba(65, 198, 196, 1)","rgba(51, 110, 147, .7)", "rgba(38, 168, 73, .7)", "rgba(99, 99, 97, .7)", "rgba(198, 85, 85, .7)", "rgba(198, 161, 85, .7)", "rgba(65, 198, 196, .7)"],
                       'categorical-7': ["rgba(51, 110, 147, .7)", "rgba(38, 168, 73, .7)", "rgba(99, 99, 97, .7)", "rgba(198, 85, 85, .7)", "rgba(198, 161, 85, .7)", "rgba(65, 198, 196, .7)","rgba(51, 110, 147, .5)", "rgba(38, 168, 73, .5)", "rgba(99, 99, 97, .5)", "rgba(198, 85, 85, .5)", "rgba(198, 161, 85, .5)", "rgba(65, 198, 196, .5)","rgba(51, 110, 147, .3)", "rgba(38, 168, 73, .3)", "rgba(99, 99, 97, .3)", "rgba(198, 85, 85, .3)", "rgba(198, 161, 85, .3)", "rgba(65, 198, 196, .3)"],
                       'categorical-5': ["rgba(51, 110, 147, .5)", "rgba(38, 168, 73, .5)", "rgba(99, 99, 97, .5)", "rgba(198, 85, 85, .5)", "rgba(198, 161, 85, .5)", "rgba(65, 198, 196, .5)"],
                       'categorical-3': ["rgba(51, 110, 147, .3)", "rgba(38, 168, 73, .3)", "rgba(99, 99, 97, .3)", "rgba(198, 85, 85, .3)", "rgba(198, 161, 85, .3)", "rgba(65, 198, 196, .3)"]
                      }
        
    def html(self, html_id='', **kwargs):
        #Allow defining table ID for reference by JS
        if html_id == '':
            classes = 'table table-hover table-small-row'
        else:
            classes = 'table table-hover table-small-row" id="{}'.format(html_id)
            
        return self.df.to_html(
            classes = classes,
            escape=False,
            index=False,
            border = 0, 
            float_format=lambda x:'{:,.0f}'.format(x) if (x > 999) else '{:,.1f}'.format(x))

    def chartjs_data(self, data_col_list=[], index_col_list=[], cumulative=False, round=0, pallet_name="categorical"):
        
        df = self.df.copy() #[['Spent','Remaining']]
        pallet = self.pallet[pallet_name]
        pallet_fill = self.pallet[pallet_name + '-7']
        #Set Data Columns from arguments
        if isinstance(index_col_list, (list, str)) and (len(index_col_list) > 0):
            df = df.set_index(index_col_list)
            
        #Set Data Columns from arguments
        if isinstance(data_col_list, (list, str)) and (len(data_col_list) > 0):
            df = df[data_col_list]
        
        #print(type(df.index))
        if isinstance(df.index,pd.PeriodIndex):
            df.index = df.index.strftime("%b'%y")
        if df.index.name == 'date':
            df.index = pd.to_datetime(df.index).strftime("%b'%y")
        
        
        df = df.round(round)
        #Run Cuulative Sum if Desired
        if cumulative:
            df = df.cumsum().fillna('null')
        else:
            df = df.fillna('null')
        
        data = {'labels':df.index.tolist()}
        rec = []
        for i, c in enumerate(df.columns):
            d = {'label' : c,
                 'data' : df[c].tolist(), #round(round)
                 'borderWidth': 1,
                 'lineColor': pallet[i],
                 'borderColor': pallet[i],
                 'backgroundColor': pallet_fill[i]}
            #if isinstance(chart_types, list):
            #    d['type'] = chart_types[i]
            rec.append(d)
        data['datasets'] = rec
        return data
    
    def datatables(self):
        df = self.df.copy()
        #if isinstance(df.iloc[0,0], date):
        #    df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
        #    df[df.columns[0]] = df[df.columns[0]].dt.strftime('%b-%y')
        df = df.set_index(df.columns[0])
        data = df.values.tolist()
        rnames = df.columns.tolist()
        #for i in range(0,len(data)):
        #    data[i].insert(0,rnames[i])
        
        #Pull out (new transposed) Column Defs
        cnames = []
        [cnames.append({"title":i}) for i in rnames]
        cnames.append([{"className":'details-control',
                "orderable":False,
                "data":'null',
                "defaultContent": ''}])
        dt_dict = {}
        dt_dict['data'] = data
        dt_dict['columns'] = cnames
        return dt_dict
        
