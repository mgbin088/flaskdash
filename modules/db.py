import sqlalchemy as sa
import pandas as pd
from sqlalchemy import Table, select

def query_json():
    cur_schema = 'pce'

    eng = sa.create_engine('postgres://ben:Sm00chm3!@server2:5432/cca')
    meta = sa.MetaData()
    view = Table('invoice_record_counts', meta, autoload=True, autoload_with=eng, schema = cur_schema)

    #p = ['2017-09-01','2017-09-02']
    qry = view.select()  #.where(mdef.c.trade_date.in_(p))
    results = pd.read_sql(qry, eng)
    results.day = pd.to_datetime(results.day).dt.strftime('%Y-%m-%d')
    return results.to_json(orient='records')

if __name__ == "__main__":
    print(query_json())