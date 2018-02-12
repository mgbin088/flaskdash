from .database import Base, get_or_create
from flask_security import UserMixin, RoleMixin

from sqlalchemy import create_engine, types, MetaData, Table, or_, UniqueConstraint, \
                       Boolean, DateTime, Column, Integer, \
                       String, ForeignKey, Text, Boolean, ARRAY
from sqlalchemy.sql import select

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
    users = relationship("User", secondary='clients_users', back_populates="client")

######################################################################
##                    BUDGET TRACKER MODELS
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
    path_id = Column("path_id", ARRAY(Integer))
    path_name = Column("path_name", ARRAY(Text))
    depth = Column(Integer)
    parent = relationship("HeirarchyNode", remote_side=[id])
    client = relationship("Client")
    version = relationship("HeirarchyVersion")
    #children = relationship("Node",
    #           backref=backref('parent', remote_side=[id]))
    
#class HeirarchyNodeDetail(Base):
#    """This is a view already created in SQL that flattens the heirarchy"""
#    __tablename__ = 'budget_node_detail'
#    client_id = Column(Integer)
#    client_name = Column(Text)
#    id = Column(Integer, primary_key=True)
#    name = Column(Text)
#    ancestors = Column("ancestors", ARRAY(Integer))
#    tree = Column("tree", ARRAY(Text))
#    depth = Column(Integer)
#    cycle = Column(Boolean)

############################
#### 
###########################
