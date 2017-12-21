#Environment
import os
from datetime import datetime, date
import pandas as pd
#data_path = 'e:\\BenProjects\\flaskdash\\data\\'
data_path = '/var/www/data/'
pd.set_option('display.float_format', lambda x: '%.3f' % x)


def invoice_usage_matrix(company, value_col, date_from='', date_to=''):
    #Load DataFrame from File
    ifile = os.path.join(data_path,'{}_invoice_vs_load_comparison.csv'.format(company))
    df = pd.read_csv(ifile, parse_dates=['usage_month','invoice_month'])

    ##Set and clean variables / column names
    date_from = date_from #NEED TO ADD CHECK FOR DATE VS STRING VS INT  #date(2016,11,1).strftime('%Y%m%d')
    date_to = date_to #NEED TO ADD CHECK FOR DATE VS STRING VS INT  #date(2017,11,1).strftime('%Y%m%d')
    row_idx = 'invoice_month'
    col_idx = 'usage_month'
    value_col = value_col
    
    if not value_col in df.columns:
        raise ValueError('invalid value column provided')
        
    #Filter
    filt = "{} >= {} & {} <= {}".format(col_idx,date_from,col_idx,date_to)
    #Aggregate
    f_inv = df[[col_idx,row_idx,value_col]].query(filt) \
        .groupby([col_idx,row_idx]) \
        .agg({value_col:sum}) \
        .reset_index()
    
    f_inv['usage_total_kwh'] = (f_inv['usage_total_kwh']/1000000).round(1)
    f_inv[col_idx] =  pd.to_datetime(f_inv[col_idx], format="%Y-%m-%d %H:%M:%S").dt.strftime("%Y-%m")
    
    ## Pivot
    f_pvt = f_inv.pivot_table(index=row_idx,columns=col_idx, \
                      values=value_col, margins=True, \
                      aggfunc=sum, margins_name='Total') \
        .fillna('').replace(0.,'') #empty strings for NaN and 0 values
    f_pvt.index = smart_strftime(f_pvt.index) #, format="%Y-%m-%d %H:%M:%S").dt.strftime("%b'%y")    
    f_pvt.columns = smart_strftime(f_pvt.columns) #, format="%Y-%m-%d %H:%M:%S").dt.strftime("%b'%y")    
    return f_pvt

def df_to_dt(df):
    data = df.values.tolist()
    rnames = df.columns.tolist()
    for i in range(0,len(rnames)):
        data[i].insert(0,rnames[i])

    #Pull out (new transposed) Column Defs
    cnames = [{"title":"Metric"}]
    [cnames.append({"title":i}) for i in df.index]
    return data, cnames

def smart_strftime(s):
    newnames = []
    for i in s:
        try:
            #print(type(i))
            x = pd.to_datetime(i).strftime("%b'%y")
            newnames.append(x)
        except:
            #print('except {}'.format(i))
            newnames.append(i)
    return newnames


if __name__ == "__main__":
    dt, col = df_to_dt(invoice_usage_matrix('pce','usage_total_kwh', 20161101, 20171101))
    print(dt)
    print(col)

