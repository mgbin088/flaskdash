from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, and_
from sqlalchemy.dialects.postgresql import ARRAY, JSON
#from sqlalchemy.ext.associationproxy import association_proxy
db = SQLAlchemy()
######################################################################

class BudgetActual(db.Model):
    __table__ = db.Table('v_budget_actual', db.metadata,
        db.Column('node_id', db.Integer, primary_key=True),
        db.Column('period', db.Date, primary_key=True),
        db.Column('actual', db.Numeric),
        db.Column('budget', db.Numeric),
        db.Column('name', db.Text),
        db.Column('client_id', db.Integer),
        db.Column('path_name', ARRAY(db.Text)),
        db.Column('path_id', ARRAY(db.Integer)),
        )
    
class Calendar(db.Model):
    __table__ = db.Table("calendar", db.metadata,
                db.Column("date_actual", db.Date, primary_key=True),
                autoload=True, autoload_with=db.engine
                )
                
class TransactionDetail(db.Model):
    __table__ = db.Table("v_transactions", db.metadata,
                db.Column("id", db.Integer, primary_key=True),
                autoload=True, autoload_with=db.engine
                )

#class BudgetSpendJsonX(db.Model):
#    __table__ = db.Table("v_spend_by_line_json", db.metadata,
#                db.Column("budget", db.Text, primary_key=True),
#                db.Column("vendor", db.Text, primary_key=True),
#                db.Column("path_id", ARRAY(db.Integer)),
#                db.Column("spend_obj", JSON),
                #autoload=True, autoload_with=engine
#                )

class BudgetSpendJson(db.Model):
    __table__ = db.Table("v_spend_by_line_json", db.metadata,
                db.Column("budget", db.Text, primary_key=True),
                db.Column("vendor", db.Text, primary_key=True),
                db.Column("period", db.Date, primary_key=True),                      
                db.Column("path_id", ARRAY(db.Integer)),
                db.Column("doc", JSON),
    )                
                
def get_budget_actual(node_id, fiscal_year=None, fyear_start_mo=None,client=None):
    '''Get budget actual query, filtered by node (with all children) and filtered by fiscal year'''
    if not client and not fyear_start_mo:
        print("need fiscal year start or client")
    
    if not fiscal_year:
        fiscal_year = 2018
    
    if not fyear_start_mo:
        fiscal_year = 1
    
    q = db.session.query(BudgetActual.path_name, BudgetActual.period, BudgetActual.actual, BudgetActual.budget).join(Calendar, BudgetActual.period==Calendar.date_actual)
    q = q.filter(BudgetActual.path_id.any(node_id))
    q = q.filter(BudgetActual.client_id==1, Calendar.__dict__['fiscal_year_{}'.format(str(fyear_start_mo))] == fiscal_year)
    return q