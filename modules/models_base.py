from .database import Base, get_or_create
from flask_security import UserMixin, RoleMixin

from sqlalchemy import create_engine, types, MetaData, Table, or_, UniqueConstraint, \
                       Boolean, Date, DateTime, Column, Integer, Numeric, \
                       String, ForeignKey, Text, Boolean, ARRAY, func, FetchedValue
from sqlalchemy.sql import select
from sqlalchemy.ext.associationproxy import association_proxy

from sqlalchemy.orm import relationship, backref



######################################################################
##                    USER AND CLIENT
######################################################################


class RolesUsers(Base):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))

class Role(Base, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))

class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    firstname = Column(String(255))
    lastname = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='roles_users', backref=backref('users', lazy='dynamic'))
    client = relationship("Client", secondary='clients_users', back_populates="users")

    
    
class ClientsUsers(Base):
    __tablename__ = 'clients_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    client_id = Column('client_id', Integer(), ForeignKey('client.id'))

class Client(Base):
    __tablename__ = 'client'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), unique=True)
    domain = Column(String(100), unique=True)
    abbreviation = Column(String(10), unique=True)
    fyear_start_mo = Column(Integer())
    users = relationship("User", secondary='clients_users', back_populates="client")

######################################################################
##                    REPORT HEIRARCHY's
######################################################################

class HeirarchyVersion(Base):
    __tablename__ = 'heirarchy_version'
    __table_args__ = (UniqueConstraint('client_id', 'name'),)
    id = Column(Integer, primary_key=True)
    client_id =  Column(ForeignKey('client.id'))
    name = Column(Text, default="budget")
    description = Column(Text)
    levels = Column(ARRAY(Text))
    client = relationship("Client")
    
    
class HeirarchyNode(Base):
    __tablename__ = 'heirarchy_node'
    __table_args__ = (UniqueConstraint('client_id', 'heirarchy_id', 'name'),)
                    
    id = Column(Integer, primary_key=True)
    heirarchy_id = Column(Integer, ForeignKey('heirarchy_version.id'))
    parent_id = Column(Integer, ForeignKey('heirarchy_node.id'))
    client_id = Column(ForeignKey('client.id'))
    name = Column(Text, unique=True, nullable=False)
    name_short = Column(Text)
    description = Column(Text)
    path_id = Column("path_id", ARRAY(Integer), server_default=FetchedValue())
    path_name = Column("path_name", ARRAY(Text), server_default=FetchedValue())
    depth = Column(Integer, server_default=FetchedValue())
    leaf_flag = Column(Boolean)
    
    #parent = relationship("HeirarchyNode", remote_side=[id])
    client = relationship("Client")
    version = relationship("HeirarchyVersion")
    children = relationship("HeirarchyNode",
               backref=backref('parent', remote_side=[id]),
               join_depth=2)
    client_abbrev = association_proxy('client','abbreviation')


class TxnNodeAssign(Base):
    __tablename__ = 'transaction_node_assign'
    #Keys
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('client.id'))
    node_id = Column(Integer, ForeignKey('heirarchy_node.id'), nullable=False)
    
    #Business Rules to associate transactions with Nodes in the Heirarchy
    account_id = Column(ForeignKey('chart_accounts.id'), nullable=False, )
    project_vendor_id = Column(ForeignKey('vendor.id'))
    project_customer_id = Column(ForeignKey('project_customer.id'))
    project_class_id = Column(ForeignKey('project_class.id'))     
    
    #
    active = Column(Boolean, default = True)
    comments = Column(Text)
    

#################################################################
####                 BUDGET MODEL
#################################################################

class BudgetVersion(Base):
    __tablename__ = 'budget_version'
    #__table_args__ = (UniqueConstraint('client_id', 'name'),)
    id = Column(Integer, primary_key=True)
    client_id =  Column(ForeignKey('client.id'), nullable=False)
    name = Column(Text, nullable=False)
    revision = Column(Text)
    description = Column(Text)
    active = Column(Boolean, default=True)
    heirarchy_id = Column(Integer, ForeignKey('heirarchy_version.id'), nullable=False)
    client = relationship("Client")
    heirarchy = relationship("HeirarchyVersion")

    
class Budget(Base):
    __tablename__ = 'budget'
    __table_args__ = (UniqueConstraint('node_id', 'budget_id','period','metric'),)

    #Columns (ID's)
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('client.id'), nullable=False)
    #heirarchy_id = Column(Integer, ForeignKey('heirarchy_version.id'), nullable=False) #this might be redundant with HeirarchyID
    node_id = Column(Integer, ForeignKey('heirarchy_node.id'),nullable=False)
    budget_id = Column(ForeignKey('budget_version.id'), nullable=False)

    #Columns (Facts)
    period = Column(Date, nullable=False)
    metric = Column(Text, default = 'amount', nullable=False)
    value = Column(Numeric, nullable=False) 
    
    #Meta
    created_user_id = Column(ForeignKey('user.id'))
    created_ts = Column(DateTime, nullable=False, server_default=func.statement_timestamp())
    updated_user_id = Column(ForeignKey('user.id'))
    updated_ts = Column(DateTime, nullable=False, server_default=func.statement_timestamp(), onupdate=func.statement_timestamp())
    
    #Relationships
    budget = relationship("BudgetVersion")
    #heirarchy = relationship("HeirarchyVersion")
    client = relationship("Client")
    node = relationship("HeirarchyNode")
    user_updated = relationship("User", foreign_keys=[updated_user_id])
    user_created = relationship("User", foreign_keys=[created_user_id])

############################################################################################
####   QUICKBOOKS DATA
############################################################################################


class ChartAccounts(Base):
    __tablename__ = 'chart_accounts'
    #__table_args__ = (UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('client.id'), nullable=False)
    name = Column(Text)
    description = Column(Text)
    account_type = Column(Text)
    active = Column(Boolean)
    created_ts = Column(DateTime)
    updated_ts = Column(DateTime)
    path_id = Column(ARRAY(Integer))
    path_name = Column(ARRAY(Text))
    parent_id = Column(Integer)
    #QB id's for reference
    qb_id = Column(Text)
    qb_fullname = Column(Text)
    qb_parent_id = Column(Text)
        
class VendorCustomer(Base):
    __tablename__ = 'vendor_customer'
    __table_args__ = (UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('client.id'), nullable=False)
    name = Column(Text)
    active = Column(Boolean)
    project_flag = Column(Boolean)
    
    created_ts = Column(DateTime)
    updated_ts = Column(DateTime)
    #QB id's for reference
    qb_id = Column(Text, nullable=False, unique=True)

class ProjectCustomer(Base):
    __tablename__ = 'project_customer'
    __table_args__ = (UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('client.id'), nullable=False)
    name = Column(Text)
    active = Column(Boolean)
    created_ts = Column(DateTime)
    updated_ts = Column(DateTime)

    parent_id = Column(Integer)
    class_id = Column(Integer)
    path_id = Column(ARRAY(Integer))
    path_name = Column(ARRAY(Text))
    #QB id's for reference
    qb_class_id = Column(Text)
    qb_id = Column(Text, nullable=False, unique=True)
    qb_parent_id = Column(Text)

class ProjectClass(Base):
    __tablename__ = 'project_class'
    #__table_args__ = (UniqueConstraint('client_id', 'qb_id'),)
    
    #Columns (ID's)
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('client.id'), nullable=False)
    name = Column(Text)
    active = Column(Boolean)
    created_ts = Column(DateTime)
    updated_ts = Column(DateTime)
    #QB id's for reference
    qb_id = Column(Text, nullable=False, unique=True)
    qb_parent_id = Column(Text)
    
        
def account_id_from_qb(context):
    qid = context.get_current_parameters()['qb_account_id']
    return ChartAccounts.__table__.select('id', limit=1).where(ChartAccounts.__table__.c.qb_id==qid)
    
        
class Transactions(Base):
    __tablename__ = 'gl_transactions'
    #__table_args__ = (UniqueConstraint('client_id', 'txn_number'),)
    
    #Columns (ID's)
    id = Column(Integer, primary_key=True)
    client_id = Column(ForeignKey('client.id'), nullable=False)
    
    account_id = Column(ForeignKey('chart_accounts.id'), default=account_id_from_qb)
    vendor_id = Column(ForeignKey('vendor_customer.id'))
    project_customer_id = Column(ForeignKey('vendor_customer.id'))
    project_class_id = Column(ForeignKey('project_class.id'))
    
    budget_node_id = Column(ForeignKey('heirarchy_node.id'))
    
    txn_number = Column(Integer)
    #account_number = Column(Text)  ##should be foregn
    #account_name = Column(Text)  ##should be foregn
    txn_type = Column(Text)
    date = Column(Date)
    #month = Column(Date, default=func.date_trunc('month', date))  ##auto to speed up aggregation
    #fiscal_year = Column(Integer)  ## should be foreign
    ref_num = Column(Text)
    name = Column(Text)  ##should be foregn
    memo = Column(Text)
    #split = Column(Text)
    amount = Column(Numeric)
    
    account = relationship("ChartAccounts", foreign_keys=[account_id])
    vendor = relationship("VendorCustomer", foreign_keys=[vendor_id])
    project_customer = relationship("VendorCustomer", foreign_keys=[project_customer_id])
    project_class = relationship("ProjectClass")
    heirarchy = relationship("HeirarchyNode")
