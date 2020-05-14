import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

database_url = os.getenv('DATABASE_URL')

Base = declarative_base()

engine = create_engine(database_url)


from sqlalchemy_bigid.testapp import models   # noqa
