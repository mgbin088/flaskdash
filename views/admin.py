from flask import current_app, Blueprint, render_template, Response
admin = Blueprint('admin', __name__, url_prefix='/admin')

from flask_security import login_required, current_user, roles_required
from mahercpa.modules.models import *

@roles_required('admin')
@admin.route('/init')
def populate_new_db():
    from flask_security.utils import encrypt_password
    #init_db()
    #user_client = db.session.query(Client).filter_by(abbreviation='MCE').first()
    #print(user_client.name)
    mce = Client(name='Marin Clean Energy', domain='mcecleanenergy.org',abbreviation='MCE')
    svce = Client(name='Silicon Valley Clean Energy', domain='svcleanenergy.org',abbreviation='SVCE')
    scp = Client(name='Sonoma Clean Power', domain='sonomacleanpower.org',abbreviation='SCP')
    pce = Client(name='Peninsula Clean Energy', domain='peninsulacleanenergy.com',abbreviation='PCE')
    #maher = Client(name='Maher Accountancy', domain='mahercpa.com',abbreviation='MAHER')
    for c in [mce,scp,pce,svce]:
        db.session.add(c)
    
    user_datastore.create_user(email='bmaher@mahercpa.com', password=encrypt_password('password'), confirmed_at=datetime(2017,1,1))
    user_datastore.create_user(email='ben@benjaminmaher.com', password=encrypt_password('password'), confirmed_at=datetime(2017,1,1))
    
    for r in ['admin','mce','scp','pce','svce']:
        user_datastore.create_role(name=r)

    db.session.commit()
    
    #Assing Default Roles
    for r in ['admin','mce','scp','pce','svce']:
        user_datastore.add_role_to_user(user_datastore.get_user('bmaher@mahercpa.com'), r)
    
    user_datastore.add_role_to_user(user_datastore.get_user('ben@benjaminmaher.com'), 'scp')
    
    #Assing Default Clients
    user = user_datastore.get_user('bmaher@mahercpa.com')
    for c in [mce,scp,pce,svce]:
        c.users.append(user)
    
    scp.users.append(user_datastore.get_user('ben@benjaminmaher.com'))
    
    
    db.session.commit()
    return Response('OK!')
    
@admin.route("/users/delete/<user_name>")
@login_required
@roles_required('admin')
def delete_user(user_name):
    user = user_datastore.get_user(user_name)
    user_datastore.delete_user(user)
    db.session.commit()
    return Response(user_name)

@admin.route("/roles/create/<role_name>")
@login_required
@roles_required('admin')
def add_role(role_name):
    user_datastore.create_role(name=role_name)
    db.session.commit()
    return Response(role_name)

@admin.route("/client/assign/<client>/<user_name>")
@login_required
@roles_required('admin')
def add_user_to_client(client, user_name):
    client = db.session.query(Client).filter_by(abbreviation=client.upper()).first()
    user = user_datastore.get_user(user_name)
    print(client.name)
    print(user.email)
    if client is not None and user is not None:
        print(client.name, user.email)
        client.users.append(user)
        db.session.commit()
    return Response(user.email)

@admin.route("/roles/assign/<user>/<role>")
@login_required
@roles_required('admin')
def add_role_to_user(user, role):
    print(user, role)
    user_datastore.add_role_to_user(user, role)
    db.session.commit()
    return Response(role)

@admin.route("/me")
@login_required
def whoami():
    user = user_datastore.get_user(current_user.email)
    client_list = "client(s): " + ','.join([i.domain for i in user.client])
    role_list = "roles(s): " + ','.join([i.name for i in user.roles])
    return Response(user.email + ": " + client_list + "; " + role_list)