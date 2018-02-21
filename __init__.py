import flask
import flask_sqlalchemy
import flask_restless
from flask_security import Security, SQLAlchemySessionUserDatastore, user_registered #, UserMixin, RoleMixin, login_required, utils, core
from flask_mail import Mail

# Create the Flask-Restless API manager.
db = flask_sqlalchemy.SQLAlchemy()
mail = Mail()
security = Security()
apimanager = flask_restless.APIManager(flask_sqlalchemy_db=db)

def create_app(config_name=None):
# Create the database tables.
    app = flask.Flask(__name__)
    if not config_name:
        app.config.from_envvar('FLASKDASH_SETTINGS')
    else:
        app.config.from_pyfile(config_name)
    
    #app.config['DEBUG'] = True
    #'SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://mahercpa_app:h2%7N%Jzn&&f@mahercpa.cal45ovofuod.us-west-2.rds.amazonaws.com:5432/dev'
    
    from mahercpa.modules.models import db, Budget, BudgetVersion, Client, User, Role, user_datastore
    db.init_app(app)
    mail.init_app(app)
    #user_datastore = SQLAlchemySessionUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)

    # This processor is added to only the register view
    @user_registered.connect_via(app)
    def user_registered_sighandler(sender, user, confirm_token):
        #print("print-user_registered_sighandler:", user.email)
        user_domain = str(user.email).split('@')[1]
        #print(user_domain)
        user_client = db_session.query(Client).filter_by(domain=user_domain).first()
    
        if user_client is not None:
            print(user_client.name)
            user_client.users.append(user)
            db_session.commit()
        

    user_registered.connect(user_registered_sighandler)
    
    apimanager.init_app(app=app) #Don't pass in db a second time, just the app object
    
    # Create API endpoints, which will be available at /api/<tablename> by
    # default. Allowed HTTP methods can be specified as well.
    with app.app_context():
        client_cols = ['name','abbreviation','domain']
        apimanager.create_api(Client, methods=['GET'], include_columns=client_cols, app=app)
        apimanager.create_api(BudgetVersion, methods=['GET','POST'], results_per_page=100, app=app)
    
    from mahercpa.views.main import main
    app.register_blueprint(main)
    
    from mahercpa.views.bud_track import bud_track
    app.register_blueprint(bud_track)
    
    from mahercpa.views.admin import admin
    app.register_blueprint(admin)
    
    from mahercpa.views.dash_revenue import dash_revenue
    app.register_blueprint(dash_revenue)
    
    return app
