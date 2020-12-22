"""
Import this module to override Alembic migration-generation behavior for bigid

https://alembic.sqlalchemy.org/en/latest/api/autogenerate.html#registering-a-comparison-function
"""
from alembic.autogenerate import comparators, rewriter, renderers
from alembic.operations import ops, Operations, MigrateOperation
from sqlalchemy import DDL

from sqlalchemy_bigint_id.utils import get_bigid_column_from_table
from sqlalchemy_bigint_id.schema import generate_nextbigid_sql, get_nextbigid_function_text


writer = rewriter.Rewriter()


@writer.rewrites(ops.CreateTableOp)
def create_table(context, revision, op):
    """
    Check if there is a BigID column (BigInteger marked as needing nextbigid)
    and then emit the SQL migration to set the default
    """
    bigid_column = get_bigid_column_from_table(op._orig_table)

    if bigid_column is not None:
        # Generate SQL to set default for the col to call nextbigid()
        sql = generate_nextbigid_sql(op.table_name, bigid_column.key)
        nextbigid_op = ops.ExecuteSQLOp(sql)
        return [
            op,
            nextbigid_op
        ]
    else:
        return op


@Operations.register_operation("create_nextbigid_function")
class CreateNextBigIdFunctionOp(MigrateOperation):
    @classmethod
    def create_nextbigid_function(cls, operations, **kw):
        op = CreateNextBigIdFunctionOp(**kw)
        return operations.invoke(op)

    def reverse(self):
        return DropNextBigIdFunctionOp()


@Operations.register_operation("drop_nextbigid_function")
class DropNextBigIdFunctionOp(MigrateOperation):
    @classmethod
    def drop_nextbigid_function(cls, operations, **kw):
        op = DropNextBigIdFunctionOp(**kw)
        return operations.invoke(op)


@Operations.implementation_for(CreateNextBigIdFunctionOp)
def create_nextbigid_function(operations, operation):
    function_text = get_nextbigid_function_text()
    operations.execute(DDL(function_text))


@Operations.implementation_for(DropNextBigIdFunctionOp)
def drop_nextbigid_function(operations, operation):
    operations.execute('drop function nextbigid')


@renderers.dispatch_for(CreateNextBigIdFunctionOp)
def render_create_nextbigid_function(autogen_context, op):
    return "op.create_nextbigid_function()"


@renderers.dispatch_for(DropNextBigIdFunctionOp)
def render_drop_nextbigid_function(autogen_context, op):
    return "op.drop_nextbigid_function()"


@comparators.dispatch_for("schema")
def compare_sequences(autogen_context, upgrade_ops, schemas):
    """
    Insert operation to create nextbigid function for the very first migration
    """
    # Is initial migration if either no alembic_version, or no version_num there
    conn = autogen_context.connection
    try:
        result = list(conn.execute('select * from alembic_version limit 1'))
        is_initial_migration = (not result)
    except Exception:
        is_initial_migration = True

    if is_initial_migration:
        print('Initial migration detected, no tables yet')
        nextbigid_op = CreateNextBigIdFunctionOp()
        upgrade_ops.ops.insert(0, nextbigid_op)
