from modules.database import Base
from flask_security import UserMixin, RoleMixin
from sqlalchemy import create_engine, types
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey

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
    username = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean())
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))

class Budget_line(Base):
    __tablename__ = 'budget_line'
    id = Column(Integer(), primary_key=True)
    budget_line = Column('budget_line', String(255))
    department_id = Column('department_id',Integer(),ForeignKey('budget_department.id'))

class Budget_department(Base):
    __tablename__ = 'budget_department'
    id = Column(Integer(), primary_key=True)
    department = Column('budget_line', String(255))
   
class Budget(Base):
    __tablename__ = 'budget'
    id = Column(Integer())
    budget_year = Column(Integer(), primary_key=True)
    budget_version = Column(Integer(), primary_key=True)
    period = Column(Integer(), primary_key=True)
    amount = Column('amount', types.Numeric(12, 2))
    volume = Column('volume', types.Numeric(12, 2))
    budget_line_id = Column('budget_line_id', Integer(), ForeignKey('budget_line.id'))
    department_id = Column('department_id', Integer(), ForeignKey('budget_department.id'))
