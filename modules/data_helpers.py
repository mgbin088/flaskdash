import pandas as pd


def get_fyear_list(start_month, includes_date=None):
    """Get a pandas series of 12 month start dates (pd Timestamp)
    for a fiscal year, given:
        start_month: Integer of First Month number in Fiscal Year
        includes_date: any date to define which fiscal year to return
    """
    if not includes_date:
        includes_date = pd.to_datetime('today')
    elif not isinstance(includes_date, pd._libs.tslib.Timestamp):
        includes_date = pd.to_datetime(includes_date)
    
    fy = pd.tseries.offsets.YearBegin(month=start_month)
    
    start_date = fy.rollback(includes_date)
    r = pd.date_range(start_date, periods=12, freq='MS')
    df = pd.DataFrame({'date':r.strftime('%Y-%m-%d'),'period_name':r.strftime('%b\'%y'),'yyyymm':r.strftime('%Y-%m')})
    return df
    

def fyear_list(include_date=None, client=None, user=None):
    """help to call get_fyear_list from context"""
    if client:
        start_month = client.fyear_start_mo
    elif user:
        start_month = user.client[0].fyear_start_mo
    else:
        raise ValueError("need user or client to get fyear start")
    
    return get_fyear_list(start_month, include_date)
        
    
        