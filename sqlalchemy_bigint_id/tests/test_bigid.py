import os

import pytest
from sqlalchemy import Column, Text
from alembic import command
from alembic.autogenerate import render_python_code, produce_migrations
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations, ops

from sqlalchemy_bigint_id.schema import (
    register_nextbigid_function, generate_nextbigid_sql_for_table, setup_bigid_for_all_tables
)
from sqlalchemy_bigint_id.migration import CreateNextBigIdFunctionOp, DropNextBigIdFunctionOp
from sqlalchemy_bigint_id.utils import get_bigid_column_from_table
from sqlalchemy_bigint_id.types import BigIntegerID


@pytest.fixture
def Foo(Base):
    class Foo(Base):
        __tablename__ = 'foo'
        id = Column(BigIntegerID, primary_key=True)
        name = Column(Text)

    return Foo


@pytest.fixture
def User(Base):
    class User(Base):
        __tablename__ = 'user'
        id = Column(BigIntegerID, primary_key=True)
        name = Column(Text)

    return User


@pytest.fixture
def init_models(Foo):
    pass


def test_get_bigid_column_from_table(Foo):
    assert get_bigid_column_from_table(Foo.__table__) == Foo.id


def test_generate_nextbigid_sql(Foo, User):
    sql = generate_nextbigid_sql_for_table(Foo.__table__)
    assert sql == """ALTER TABLE foo ALTER COLUMN id set default nextbigid('foo_id_seq')"""

    sql = generate_nextbigid_sql_for_table(User.__table__)
    assert sql == """ALTER TABLE "user" ALTER COLUMN id set default nextbigid('user_id_seq')"""


def test_register_bigid_function(Base, engine, connection):
    # Just test for coverage, what can we test for?
    register_nextbigid_function(metadata=Base.metadata)
    Base.metadata.create_all(engine)


def test_setup_bigid_for_all_tables(Base, Foo, User, session, engine):
    setup_bigid_for_all_tables(Base.metadata)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    foo = Foo(name='foo')
    session.add(foo)
    session.commit()

    # Check that the ID is indeed large
    assert foo.id > 10000000


def test_alembic_nextbigid_ops(engine):
    # Test the migration operations work
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        op = Operations(context)
        op.create_nextbigid_function()
        op.drop_nextbigid_function()


def test_alembic_autogenerate_nextbigid(Foo, connection, Base, engine):
    from sqlalchemy_bigint_id import migration  # noqa

    context = MigrationContext.configure(
        connection=connection,
    )
    migration_script = produce_migrations(context, Base.metadata)
    first_upgrade_op = migration_script.upgrade_ops.ops[0]
    assert isinstance(first_upgrade_op, CreateNextBigIdFunctionOp)


def test_alembic_render_bigid_function_ops():
    upgrade_code = render_python_code(ops.UpgradeOps(ops=[CreateNextBigIdFunctionOp()]))
    downgrade_code = render_python_code(ops.DowngradeOps(ops=[DropNextBigIdFunctionOp()]))
    assert 'op.create_nextbigid_function()' in upgrade_code
    assert 'op.drop_nextbigid_function()' in downgrade_code


def test_alembic_migration():
    from sqlalchemy_bigint_id.testapp import db  # noqa
    config = Config("alembic.ini")
    result = command.revision(config, message='initial', autogenerate=True)

    migration_filepath = result.path

    with open(migration_filepath) as file:
        content = file.read()

    assert 'op.create_nextbigid_function' in content
    assert """ALTER TABLE coin ALTER COLUMN id set default nextbigid('coin_id_seq')""" in content

    # Clean it up
    os.remove(migration_filepath)
