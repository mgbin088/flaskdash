from flask import current_app, Blueprint, render_template, Response
from flask_security import Security, SQLAlchemySessionUserDatastore, UserMixin, RoleMixin, login_required, roles_required, roles_accepted, utils, core, current_user
budget_views = Blueprint('budget_views', __name__) #, url_prefix='/'

from .models import *
from .data_helpers import *

@login_required
@budget_views.route("/bbudget")
def home():
    months = (fyear_list(include_date='2018-01-14', user=current_user)
              .strftime('%Y-%m-%d').tolist())
    
    return render_template('makebudget.html', months=months)
    