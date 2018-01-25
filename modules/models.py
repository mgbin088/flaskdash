from .database import Base
from flask_security import UserMixin, RoleMixin
from sqlalchemy import create_engine, types
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey

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

#class BudgetProject(Base):
#    __tablename__ = 'budget_project'
#    id = Column(Integer(), primary_key=True)
#    project = Column('budget_project', String(255))
#    parent_id = Column('parent_id',Integer(),ForeignKey('budget_line.id'))
#    client_id = Column('client_id', Integer(), ForeignKey('client.id'))
#    parent = relationship("BudgetLine", back_populates="budget_project")

#class BudgetLine(Base):
#    __tablename__ = 'budget_line'
#    id = Column(Integer(), primary_key=True)
#    line = Column('budget_line', String(255))
#    parent_id = Column('department_id',Integer(),ForeignKey('budget_department.id'))
#    client_id = Column('client_id', Integer(), ForeignKey('client.id'))
#    parent = relationship("BudgetDepartment", back_populates="budget_line")

#class BudgetDepartment(Base):
#    __tablename__ = 'budget_department'
#    id = Column(Integer(), primary_key=True)
#    department = Column('budget_line', String(255))
#    client_id = Column('client_id', Integer(), ForeignKey('client.id'))

   
#class Budget(Base):
#    __tablename__ = 'budget'
#    id = Column(Integer())
#    budget_year = Column(Integer(), primary_key=True)
#    budget_version = Column(Integer(), primary_key=True)
#    period = Column(Integer(), primary_key=True)
#    amount = Column('amount', types.Numeric(12, 2))
#    volume = Column('volume', types.Numeric(12, 2))
#    budget_line_id = Column('budget_line_id', Integer(), ForeignKey('budget_line.id'))
#    department_id = Column('department_id', Integer(), ForeignKey('budget_department.id'))
#    client_id = Column('client_id', Integer(), ForeignKey('client.id'))

############################
#### Alternate Attempt for Budget Heirarchy
###########################

class BudgetLevel(Base):
    __tablename__ = 'budget_level'
    id = Column(Integer(), primary_key=True)
    client_id = Column('client_id', Integer(), ForeignKey('client.id'))
    level = Column(Integer())
    name = Column(String(255))

class BudgetHeirarchy(Base):
    __tablename__ = 'budget_heirarchy'
    id = Column(Integer(), primary_key=True)
    name = Column('name', String(255))
    description = Column('description', String(255))
    level = Column('level', Integer())
    client_id = Column('client_id', Integer(), ForeignKey('client.id'))
    parent_id = Column('parent_id', Integer(), ForeignKey('budget_heirarchy.id'))

