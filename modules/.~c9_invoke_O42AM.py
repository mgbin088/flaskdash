#import modules.data_collection as dc
import pandas as pd
pd.set_option('display.float_format', lambda x: '%.1f' % x)

class rpt_budget_dept_delete:
    def __init__(self, data_col):
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
        dfilt = "date >= '{}' & date <= '{}'".format(data_col.dates.ytd[0].strftime('%Y-%m-%d'), data_col.dates.ytd[1].strftime('%Y-%m-%d'))

        #Filter Actuals YTD and summarize by budgetline
        self.actual = (self.actual.query(dfilt)
                   .groupby(['budget_type','budget_department','budget_line','date']) #, 'account_name_x'
                   .agg({'amount':sum})
        )

        #Filter Budget YTD and summarize by budgetline
        self.budget = (self.budget.query(dfilt)
                   .groupby(['budget_type','budget_department','budget_line','date']) 
                   .agg({'budget_amount':sum})
        )

        self.budget_actual = self.actual.join(self.budget, how='outer').fillna(0)
    
    def get_budget_actual(self, budget_dept=''):
        #Test Budget Dept for Filter
        if budget_dept != '':
            filt_cat = "budget_department == '{}'".format(budget_dept)
        else:
            filt_cat = 'amount != None'
        rpt = (self.budget_actual.query(filt_cat)
             .groupby('budget_line')
             .agg(sum)
             .assign(delta = lambda df: df['budget_amount'] - df['amount'])).reset_index()
        #.pivot_table(index = ['budget_department','budget_line'],columns='date')
        return rpt 

class rpt_budget_dept:
    def __init__(self, data_col):
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
        self.actual = (self.actual.query(dt_filt_from)
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

        self.budget_actual = self.budget.join(self.actual, how='outer').fillna(0)
    
    def get_budget_actual(self, budget_dept=''):
        #Test Budget Dept for Filter
        if budget_dept != '':
            filt_cat = "budget_department == '{}'".format(budget_dept)
        else:
            filt_cat = 'amount != None'
        rpt = (self.budget_actual.query(filt_cat)
             .groupby('budget_line')
             .agg(sum)
             .assign(Remaining = lambda df: df['Budget'] - df['Spent'])).reset_index()
        #.pivot_table(index = ['budget_department','budget_line'],columns='date')
        return rpt 
        
        
class rpt_present:
    def __init__(self, dataframe):
        self.df = dataframe
        self.pallet = ['#42869E','#3c8dbc','#60B66A','#C1AA7F','#C4C7CE','#C4AFDD']
        
    def html(self, html_id='', **kwargs):
        #Allow defining table ID for reference by JS
        if html_id == '':
            classes = 'table table-hover table-small-row'
        else:
            classes = 'table table-hover table-small-row" id="{}'.format(html_id)
            
        return self.df.to_html(
            classes = classes,
            border = 0, 
            float_format=lambda x:'{:,.0f}'.format(x) if (x > 999) else '{:,.1f}'.format(x))

    def chartjs_data(self):
        df = self.df[['b''Spent','Remaining']]
        df.index = rbdf.columns[0]

        data = {'labels':df.index.tolist()}
        rec = []
        for i, c in enumerate(df.columns):
            d = {'label' : c,
                 'data' : df[c].tolist(),
                'backgroundColor': self.pallet[i],
                'stacked': 'true'
            }
            #if isinstance(chart_types, list):
            #    d['type'] = chart_types[i]
            rec.append(d)
        data['datasets'] = rec
        return data
