from sqlalchemy import (
    MetaData,
    create_engine
)
from sqlalchemy.orm import sessionmaker
from hanyuu2 import settings

metadata = MetaData()
engine = create_engine(settings.DB_URI, echo=False)
DBSession = sessionmaker(bind=engine)

def create_all():
    from hanyuu2.storage import models as _
    metadata.create_all(engine)
