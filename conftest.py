import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, configure_mappers
from sqlalchemy.ext.declarative import declarative_base

import sqlalchemy_bigid


database_url = os.environ.get('DATABASE_URL', 'postgres://root:@localhost/postgres')


sqlalchemy_bigid.configure(epoch_seconds=1514764800)


# This is a dummy thing, tests can override this to declare custom classes
@pytest.fixture
def init_models():
    pass


@pytest.fixture
def Base():
    return declarative_base()


@pytest.fixture
def engine():
    engine = create_engine(database_url)
    return engine


@pytest.fixture
def connection(engine):
    return engine.connect()


@pytest.yield_fixture
def session(engine, Base, init_models):
    configure_mappers()
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close_all()
    Base.metadata.drop_all(engine)
    engine.dispose()
