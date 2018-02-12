from mahercpa import SQLALCHEMY_DATABASE_URI #app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine(SQLALCHEMY_DATABASE_URI,   #app.config['SQLALCHEMY_DATABASE_URI']
                       convert_unicode=True)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


#####################################
## DB Helper Functions
#####################################
def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from . import models
    Base.metadata.create_all(bind=engine)
    

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def add_budget_item(session, client, name, description, parent=None, level=None):
    #validate Client
    if isinstance(client, str): 
        client = session.query(Client).filter(or_(Client.name.ilike(client), Client.abbreviation.ilike(client))).first()
    if not client:
        raise ValueError('No valid Client Provided')
    
    #Identify Parent
    if isinstance(parent, int):
        parent = session.query(BudgetHeirarchy).filter_by(item_id=parent, client_id=client.id).first()
    elif isinstance(parent, str) and len(parent) > 0:
        parent = (session.query(BudgetHeirarchy)
            .filter(BudgetMeta.name.ilike(parent))
            .filter(BudgetHeirarchy.client_id == client.id)).first()
    
    if parent:
        parent_id = parent.id
    else:
        parent_id = None
    
    #Check for Duplicate Name
    #budget_item = session.query(BudgetMeta).filter(name=name, client_id=client.id).first()
    budget_item = None
    if not budget_item:
        new_meta = BudgetMeta(name=name, description=description,level=2,client_id=client.id)
        session.add(new_meta)
        new_item = BudgetHeirarchy(client_id = client.id, parent_id = parent_id, item_id=new_meta.id)
        session.add(new_item)

        session.commit()
    #r = 'adding {} with parent: {} to client: {}'.format(name, parent.id, client.id)
    return new_item
    
