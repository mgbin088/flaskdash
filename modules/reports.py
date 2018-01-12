#import modules.data_collection as dc
import pandas as pd
pd.set_option('display.float_format', lambda x: '%.1f' % x)

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

