import pandas as pd
import os
import glob

########################################
###  TO DO STILL:
###  GET FISCAL YEAR DEFINITION FROM QB
###

def get_path():
	if os.name == 'nt':
		mountpt = '//server1/Maher/'
	else:
		mountpt = '/mnt/e/'
	data_path = mountpt + 'BenProjects/flaskdash/data/'
	return data_path

class data_collection:
    
    def __init__(self, data_path):
        self.path = data_path
        self.companies = next(os.walk(data_path))[1]
        self.data = {}
        

    def get_data(self):
        for c in self.companies:
            self.__dict__[c] = data_company_collection(c, self.path)
            self.__dict__[c].get_data()
            
class data_company_collection:
    
    def __init__(self, company, data_path):
        self.path = data_path + company + '/'
        self.data = {}
        self.data_ts = None
        
    def get_data(self):
        fpath = os.path.join(self.path, "*.csv")
        files = glob.glob(fpath)
        #d = {self.__dict__[os.path.splitext(os.path.basename(fp))[0]] = (fp) for fp in files}
        d = {os.path.splitext(os.path.basename(fp))[0]: pd.read_csv(fp) for fp in files}
        self.__dict__.update(d)
        self.get_dates()
        self.data_ts = pd.to_datetime('now')
        
    def get_dates(self):
        d = {}
        
        #First get dates from tables statistics
        self.table_statistics[['min_date','max_date']] = self.table_statistics[['min_date','max_date']].apply(pd.to_datetime)
        for r in self.table_statistics.to_dict(orient='records'):
            d[r['tbl']] = (r['min_date'], r['max_date'])
        
        #Then calculate derivatives
        #For now, assume YTD is defined by T12 data, since we get it around mid-month
        m = pd.tseries.offsets.MonthEnd()
        y = pd.tseries.offsets.YearBegin(month=7)
        q = pd.tseries.offsets.QuarterBegin(startingMonth=1)
        d['ytd'] = (y.rollback(d['T12'][1]), m.rollback(d['T12'][1]))
        d['ytdly'] = tuple(i - pd.tseries.offsets.DateOffset(years=1) for i in d['ytd'])
        d['qtd'] = (q.rollback(d['ytd'][1]), d['ytd'][1])
        d['qtdly'] = (q.rollback(d['ytdly'][1]), d['ytdly'][1])
        
        d = {k.lower(): v for k, v in d.items()}
        
        self.__dict__.update({'dates':dict_direct(d)})
        
        
class dict_direct:
    def __init__(self, dict):
        self.__dict__.update(dict)
        

