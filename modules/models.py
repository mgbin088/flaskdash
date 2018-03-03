#from .database import Base, get_or_create
#from api_app import db
#from . import db
#from sqlalchemy.ext.declarative import declarative_base
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy import types, MetaData, Table, or_,  db.UniqueConstraint, \
#                        db.Boolean, Date, DateTime, db.Column,  db.Integer, Numeric, \
#                        db.String,  db.ForeignKey,  db.Text,  db.Boolean, db.ARRAY, func, db.FetchedValue
# create_engine, 
#from sqlalchemy.sql import select
from sqlalchemy.ext.associationproxy import association_proxy
db = SQLAlchemy()
#from sqlalchemy.orm import  db.relationship, backref

#Base = declarative_base()

######################################################################
##                    USER AND CLIENT
######################################################################


class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = db.Column( db.Integer(), primary_key=True)
    user_id = db.Column('user_id',  db.Integer(),  db.ForeignKey('user.id'))
    role_id = db.Column('role_id',  db.Integer(),  db.ForeignKey('role.id'))

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column( db.Integer(), primary_key=True)
    name = db.Column( db.String(80), unique=True)
    description = db.Column( db.String(255))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column( db.Integer, primary_key=True)
    email = db.Column( db.String(255), unique=True)
    firstname = db.Column( db.String(255))
    lastname = db.Column( db.String(255))
    password = db.Column( db.String(255))
    last_login_at = db.Column(db.DateTime)
    current_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column( db.String(100))
    current_login_ip = db.Column( db.String(100))
    login_count = db.Column( db.Integer)
    active = db.Column( db.Boolean())
    confirmed_at = db.Column(db.DateTime)
    roles =  db.relationship('Role', secondary='roles_users', backref=db.backref('users', lazy='dynamic'))
    client =  db.relationship("Client", secondary='clients_users', back_populates="users")

    
    
class ClientsUsers (db.Model):
    __tablename__ = 'clients_users'
    id = db.Column( db.Integer(), primary_key=True)
    user_id = db.Column('user_id',  db.Integer(),  db.ForeignKey('user.id'))
    client_id = db.Column('client_id',  db.Integer(),  db.ForeignKey('client.id'))

class Client (db.Model):
    __tablename__ = 'client'
    id = db.Column( db.Integer(), primary_key=True)
    name = db.Column( db.String(100), unique=True)
    domain = db.Column( db.String(100), unique=True)
    abbreviation = db.Column( db.String(10), unique=True)
    fyear_start_mo = db.Column( db.Integer())
    users =  db.relationship("User", secondary='clients_users', back_populates="client")

######################################################################
##                    REPORT HEIRARCHY's
######################################################################

class HeirarchyVersion (db.Model):
    __tablename__ = 'heirarchy_version'
    __table_args__ = ( db.UniqueConstraint('client_id', 'name'),)
    id = db.Column( db.Integer, primary_key=True)
    client_id =  db.Column( db.ForeignKey('client.id'))
    name = db.Column( db.Text, default="budget")
    description = db.Column( db.Text)
    levels = db.Column(db.ARRAY( db.Text))
    client =  db.relationship("Client")
    
    
class HeirarchyNode (db.Model):
    __tablename__ = 'heirarchy_node'
    __table_args__ = ( db.UniqueConstraint('client_id', 'heirarchy_id', 'name'),)
                    
    id = db.Column( db.Integer, primary_key=True)
    heirarchy_id = db.Column( db.Integer,  db.ForeignKey('heirarchy_version.id'))
    parent_id = db.Column( db.Integer,  db.ForeignKey('heirarchy_node.id'))
    client_id = db.Column( db.ForeignKey('client.id'))
    name = db.Column( db.Text, unique=True, nullable=False)
    name_short = db.Column( db.Text)
    description = db.Column( db.Text)
    path_id = db.Column("path_id", db.ARRAY( db.Integer), server_default=db.FetchedValue())
    path_name = db.Column("path_name", db.ARRAY( db.Text), server_default=db.FetchedValue())
    depth = db.Column( db.Integer, server_default=db.FetchedValue())
    leaf_flag = db.Column( db.Boolean)
    
    #parent =  db.relationship("HeirarchyNode", remote_side=[id])
    client =  db.relationship("Client")
    version =  db.relationship("HeirarchyVersion")
    children =  db.relationship("HeirarchyNode",
               backref=db.backref('parent', remote_side=[id]),
               join_depth=2)
    client_abbrev = association_proxy('client','abbreviation')



#################################################################
####                 BUDGET MODEL
#################################################################

class BudgetVersion(db.Model):
    __tablename__ = 'budget_version'
    #__table_args__ = ( db.UniqueConstraint('client_id', 'name'),)
    id = db.Column(db.Integer, primary_key=True)
    client_id =  db.Column(db.ForeignKey('client.id'), nullable=False)
    name = db.Column(db.Text, nullable=False)
    revision = db.Column(db.Text)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    heirarchy_id = db.Column(db.Integer, db.ForeignKey('heirarchy_version.id'), nullable=False)
    client = db.relationship("Client")
    heirarchy = db.relationship("HeirarchyVersion")

    
class Budget(db.Model):
    __tablename__ = 'budget'
    __table_args__ = ( db.UniqueConstraint('node_id', 'budget_id','period','metric'),)

    #Columns (ID's)
    id = db.Column( db.Integer, primary_key=True)
    client_id = db.Column( db.ForeignKey('client.id'), nullable=False)
    #heirarchy_id = db.Column( db.Integer,  db.ForeignKey('heirarchy_version.id'), nullable=False) #this might be redundant with HeirarchyID
    node_id = db.Column( db.Integer,  db.ForeignKey('heirarchy_node.id'),nullable=False)
    budget_id = db.Column( db.ForeignKey('budget_version.id'), nullable=False)

    #Columns (Facts)
    period = db.Column(db.Date, nullable=False)
    metric = db.Column( db.Text, default = 'amount', nullable=False)
    value = db.Column(db.Numeric, nullable=False) 
    
    #Meta
    created_user_id = db.Column( db.ForeignKey('user.id'))
    created_ts = db.Column(db.DateTime, nullable=False, server_default=db.func.statement_timestamp())
    updated_user_id = db.Column( db.ForeignKey('user.id'))
    updated_ts = db.Column(db.DateTime, nullable=False, server_default=db.func.statement_timestamp(), onupdate=db.func.statement_timestamp())
    
    # db.relationships
    budget =  db.relationship("BudgetVersion")
    #heirarchy =  db.relationship("HeirarchyVersion")
    client =  db.relationship("Client")
    node =  db.relationship("HeirarchyNode")
    user_updated =  db.relationship("User", foreign_keys=[updated_user_id])
    user_created =  db.relationship("User", foreign_keys=[created_user_id])

############################################################################################
####   QUICKBOOKS DATA
############################################################################################


class ChartAccounts (db.Model):
    __tablename__ = 'chart_accounts'
    #__table_args__ = ( db.UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = db.Column( db.Integer, primary_key=True)
    client_id = db.Column( db.ForeignKey('client.id'), nullable=False)
    name = db.Column( db.Text)
    account_number = db.Column( db.Text)
    description = db.Column( db.Text)
    account_type = db.Column( db.Text)
    active = db.Column( db.Boolean)
    created_ts = db.Column(db.DateTime)
    updated_ts = db.Column(db.DateTime)
    path_id = db.Column(db.ARRAY( db.Integer))
    path_name = db.Column(db.ARRAY( db.Text))
    parent_id = db.Column( db.Integer)
    #QB id's for reference
    qb_id = db.Column( db.Text)
    qb_fullname = db.Column( db.Text)
    qb_parent_id = db.Column( db.Text)
        
class VendorCustomer (db.Model):
    __tablename__ = 'vendor_customer'
    __table_args__ = ( db.UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = db.Column( db.Integer, primary_key=True)
    client_id = db.Column( db.ForeignKey('client.id'), nullable=False)
    name = db.Column( db.Text)
    active = db.Column( db.Boolean)
    project_flag = db.Column( db.Boolean)
    
    created_ts = db.Column(db.DateTime)
    updated_ts = db.Column(db.DateTime)
    #QB id's for reference
    qb_id = db.Column( db.Text, nullable=False, unique=True)

class ProjectCustomer (db.Model):
    __tablename__ = 'project_customer'
    __table_args__ = ( db.UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = db.Column( db.Integer, primary_key=True)
    client_id = db.Column( db.ForeignKey('client.id'), nullable=False)
    name = db.Column( db.Text)
    active = db.Column( db.Boolean)
    created_ts = db.Column(db.DateTime)
    updated_ts = db.Column(db.DateTime)

    parent_id = db.Column( db.Integer)
    class_id = db.Column( db.Integer)
    path_id = db.Column(db.ARRAY( db.Integer))
    path_name = db.Column(db.ARRAY( db.Text))
    #QB id's for reference
    qb_class_id = db.Column( db.Text)
    qb_id = db.Column( db.Text, nullable=False, unique=True)
    qb_parent_id = db.Column( db.Text)

class ProjectClass (db.Model):
    __tablename__ = 'project_class'
    #__table_args__ = ( db.UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = db.Column( db.Integer, primary_key=True)
    client_id = db.Column( db.ForeignKey('client.id'), nullable=False)
    name = db.Column( db.Text)
    active = db.Column( db.Boolean)
    created_ts = db.Column(db.DateTime)
    updated_ts = db.Column(db.DateTime)
    #QB id's for reference
    qb_id = db.Column( db.Text, nullable=False, unique=True)
    qb_parent_id = db.Column( db.Text)
    
        
def account_id_from_qb(context):
    qid = context.get_current_parameters()['qb_account_id']
    return ChartAccounts.__table__.select('id', limit=1).where(ChartAccounts.__table__.c.qb_id==qid)
    
        
class Transactions (db.Model):
    __tablename__ = 'gl_transactions'
    #__table_args__ = ( db.UniqueConstraint('client_id', 'txn_number'),)
    
    #Columns (ID's)
    id = db.Column( db.Integer, primary_key=True)
    client_id = db.Column( db.ForeignKey('client.id'), nullable=False)
    
    account_id = db.Column( db.ForeignKey('chart_accounts.id'), default=account_id_from_qb)
    vendor_id = db.Column( db.ForeignKey('vendor_customer.id'))
    project_customer_id = db.Column( db.ForeignKey('vendor_customer.id'))
    project_class_id = db.Column( db.ForeignKey('project_class.id'))
    
    budget_node_id = db.Column( db.ForeignKey('heirarchy_node.id'))
    
    txn_number = db.Column( db.Integer)
    #account_number = db.Column( db.Text)  ##should be foregn
    #account_name = db.Column( db.Text)  ##should be foregn
    txn_type = db.Column( db.Text)
    date = db.Column(db.Date)
    #month = db.Column(db.Date, default=db.func.date_trunc('month', date))  ##auto to speed up aggregation
    #fiscal_year = db.Column( db.Integer)  ## should be foreign
    ref_num = db.Column( db.Text)
    name = db.Column( db.Text)  ##should be foregn
    memo = db.Column( db.Text)
    #split = db.Column( db.Text)
    amount = db.Column(db.Numeric)
    
    account =  db.relationship("ChartAccounts", foreign_keys=[account_id])
    vendor =  db.relationship("VendorCustomer", foreign_keys=[vendor_id])
    project_customer =  db.relationship("VendorCustomer", foreign_keys=[project_customer_id])
    project_class =  db.relationship("ProjectClass")
    heirarchy =  db.relationship("HeirarchyNode")
    
    
    

class TxnNodeAssign (db.Model):
    __tablename__ = 'transaction_node_assign'
    #Keys
    id = db.Column( db.Integer, primary_key=True)
    client_id = db.Column( db.ForeignKey('client.id'))
    node_id = db.Column( db.Integer,  db.ForeignKey('heirarchy_node.id'), nullable=False)
    
    #Business Rules to associate transactions with Nodes in the Heirarchy
    account_id = db.Column( db.ForeignKey('chart_accounts.id'), nullable=False, )
    project_vendor_id = db.Column( db.ForeignKey('vendor_customer.id'))
    project_customer_id = db.Column( db.ForeignKey('project_customer.id'))
    project_class_id = db.Column( db.ForeignKey('project_class.id'))     
    
    #
    active = db.Column( db.Boolean, default = True)
    comments = db.Column( db.Text)
    
    
user_datastore = SQLAlchemyUserDatastore(db, User, Role)