from sqlalchemy import (
    MetaData,
    create_engine
)
from sqlalchemy.orm import sessionmaker
from ireul import settings

metadata = MetaData()
engine = create_engine(settings.DB_URI, echo=False)
DBSession = sessionmaker(bind=engine)

def create_all():
    from ireul.storage import models as _
    metadata.create_all(engine)
