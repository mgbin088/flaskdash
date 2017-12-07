#import sqlalchemy as sa
import pandas as pd
#from sqlalchemy import Table, select
from flask import jsonify
import datetime
import os

data_path = 'e:\\BenProjects\\flaskdash\\data\\'

def query_json():
    cur_schema = 'pce'
    fname = 'pce_table_monthly_usage.csv'
    results = pd.read_csv(os.path.join(data_path, fname))
    results.usage_month = pd.to_datetime(results.usage_month).dt.strftime('%Y-%m-%d')
    return results.to_json(orient='records')


def query_usage_table():
    fname = 'pce_table_monthly_usage.csv'
    df = pd.read_csv(os.path.join(data_path, fname))
    if isinstance(df.iloc[0,0], datetime.date):
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

if __name__ == "__main__":
    print('running...')
    print(query_usage_table())
    


