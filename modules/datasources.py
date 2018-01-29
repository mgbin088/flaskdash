#import sqlalchemy as sa
import pandas as pd
#from sqlalchemy import Table, select
from flask import jsonify
#import datetime
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import os


#data_path = 'e:\\BenProjects\\flaskdash\\data\\'
data_path = '/var/www/data/'

#class latest_dates():
def get_latest_dates(client_abbreviation):
    fname = client_abbreviation + '_latest_dates.csv'
    results = pd.read_csv(os.path.join(data_path, fname))
    new_dict = {}
    for row in results.itertuples():
        new_dict[row[1]] = row[2]
    return new_dict

def get_invoice_summary(client_abbreviation):
    fname = client_abbreviation + '_invoice_summary.csv'
    results = pd.read_csv(os.path.join(data_path, fname))
    return results

def query_json():
    cur_schema = 'pce'
    fname = 'pce_table_monthly_usage.csv'
    results = pd.read_csv(os.path.join(data_path, fname))
    results.usage_month = pd.to_datetime(results.usage_month).dt.strftime('%Y-%m-%d')
    return results.to_json(orient='records')

def chartist_data(client_abbreviation, nolabels=False):
    fname = client_abbreviation + '_invoice_record_counts.csv'
    print(fname)
    df = pd.read_csv(os.path.join(data_path, fname))
    #Trim invalid dates off beginning and end
    df = df.set_index('day').sort_index()
    #df = df[['usage_total_kwh','commodity_charges']]
    df = df[['usage_total_kwh']]
    df = df.fillna("null")
    #df = df[df['usage_total_kwh'].first_valid_index():df['usage_total_kwh'].last_valid_index()]
    dtrng_start = date.today().replace(day=1)
    dtrng_end = dtrng_start + relativedelta(months=1) + relativedelta(days=-1)
    print(dtrng_start.strftime('%Y-%m-%d') + dtrng_end.strftime('%Y-%m-%d'))
    df = df[dtrng_start.strftime('%Y-%m-%d'):dtrng_end.strftime('%Y-%m-%d')]

    data = {'labels':df.index.tolist()}
    if nolabels == True:    
        rec = []
        for c in df.columns:
            rec.append(df[c].tolist())
        data['series'] = rec
    else:
        ser = []
        rec = []
        for c in df.columns:
            for ix, rw in df['usage_total_kwh'].iteritems():
                ser.append({"meta":ix,"value":rw})
            rec.append(ser)
        data['series'] = rec
    return data


def chartjs_data(data_col, client_abbreviation, chart_types=['bar','line'], nolabels=False):
    #fname = client_abbreviation + '_invoice_record_counts.csv'
    #print(fname)
    #df = pd.read_csv(os.path.join(data_path, fname))
    df = data_col.invoice_record_counts
    
    print(df.shape)
    #Trim invalid dates off beginning and end
    df = df.set_index('day').sort_index()
    #df = df[['usage_total_kwh','commodity_charges']]
    df = df[['usage_total_kwh','commodity_charges']]
    df = df.fillna("null")
    #df = df[df['usage_total_kwh'].first_valid_index():df['usage_total_kwh'].last_valid_index()]
    dtrng_start = date.today().replace(day=1)
    dtrng_end = dtrng_start + relativedelta(months=1) + relativedelta(days=-1)
    print(dtrng_start.strftime('%Y-%m-%d') + dtrng_end.strftime('%Y-%m-%d'))
    df = df[dtrng_start.strftime('%Y-%m-%d'):dtrng_end.strftime('%Y-%m-%d')]

    data = {'labels':df.index.tolist()}
    rec = []
    for i, c in enumerate(df.columns):
        d = {'label' : c,
             'data' : df[c].tolist(),
            'backgroundColor':'#FFFFFF'
        }
        if isinstance(chart_types, list):
            d['type'] = chart_types[i]
        rec.append(d)
    data['datasets'] = rec
    return data



def query_usage_table():
    fname = 'pce_table_monthly_usage.csv'
    df = pd.read_csv(os.path.join(data_path, fname))
    if isinstance(df.iloc[0,0], date):
        df[df.columns[0]] = pd.to_datetime(df[df.columns[0]])
        df[df.columns[0]] = df[df.columns[0]].dt.strftime('%b-%y')
    df = df.set_index(df.columns[0])
    data = df.T.values.tolist()
    rnames = df.columns.tolist()
    for i in range(0,len(data)):
        data[i].insert(0,rnames[i])

    #Pull out (new transposed) Column Defs
    cnames = [{"title":"Metric"}]
    [cnames.append({"title":i}) for i in df.index]
    return data, cnames



class chartData:
    def __init__(self, dataframe):
        """Return a chartData object."""
        
        self.df = dataframe

    def nolabels(self, reindex=False):
        df = self.df
        if not reindex:
            data = {'labels':df.index.tolist()}
        elif isinstance(reindex, str):
            if reindex in df.reset_index().columns:
                df = df.reset_index().set_index(reindex)
                data = {'labels':df.index.tolist()}
            else:
                raise ValueError("Invalid Index: not an existing column")
        else:
            raise ValueError("Invalid Index: must be a string")
            
        rec = []
        for c in df.columns:
            rec.append(df[c].tolist())
        data['series'] = rec
        return data
    
    def labels(self, reindex=False):
        df = self.df
        if not reindex:
            data = {'labels':df.index.tolist()}
        elif isinstance(reindex, str):
            if reindex in df.reset_index().columns:
                df = df.reset_index().set_index(reindex)
                data = {'labels':df.index.tolist()}
            else:
                raise ValueError("Invalid Index: not an existing column")
        else:
            raise ValueError("Invalid Index: must be a string")
        
        
        rec = []
        for c in df.columns:
            ser = []
            for ix, rw in df[c].iteritems():
                ser.append({"meta":ix,"value":rw})
            rec.append(ser)
        data['series'] = rec
        return data


if __name__ == "__main__":
    print('running...')
    dt, col = query_usage_table()
    print(dt)
    print(col)

