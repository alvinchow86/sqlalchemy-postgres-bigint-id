"""
Import this module to override Alembic migration-generation behavior for big int id

https://alembic.sqlalchemy.org/en/latest/api/autogenerate.html#registering-a-comparison-function
"""
from alembic.autogenerate import comparators, rewriter, renderers
from alembic.operations import ops, Operations, MigrateOperation
from sqlalchemy import DDL

from sqlalchemy_bigint_id.utils import get_bigint_id_column_from_table
from sqlalchemy_bigint_id.schema import generate_next_bigint_id_sql, get_next_bigint_id_function_text


writer = rewriter.Rewriter()


@writer.rewrites(ops.CreateTableOp)
def create_table(context, revision, op):
    """
    Check if there is a BigIntegerID column (BigInteger marked as needing next_bigint_id)
    and then emit the SQL migration to set the default
    """
    bigint_id_column = get_bigint_id_column_from_table(op._orig_table)

    if bigint_id_column is not None:
        # Generate SQL to set default for the col to call next_bigint_id()
        sql = generate_next_bigint_id_sql(op.table_name, bigint_id_column.key)
        next_bigint_id_op = ops.ExecuteSQLOp(sql)
        return [
            op,
            next_bigint_id_op
        ]
    else:
        return op


@Operations.register_operation("create_next_bigint_id_function")
class CreateNextBigIntegerIdFunctionOp(MigrateOperation):
    @classmethod
    def create_next_bigint_id_function(cls, operations, **kw):
        op = CreateNextBigIntegerIdFunctionOp(**kw)
        return operations.invoke(op)

    def reverse(self):
        return DropNextBigIntegerIdFunctionOp()


@Operations.register_operation("drop_next_bigint_id_function")
class DropNextBigIntegerIdFunctionOp(MigrateOperation):
    @classmethod
    def drop_next_bigint_id_function(cls, operations, **kw):
        op = DropNextBigIntegerIdFunctionOp(**kw)
        return operations.invoke(op)


@Operations.implementation_for(CreateNextBigIntegerIdFunctionOp)
def create_next_bigint_id_function(operations, operation):
    function_text = get_next_bigint_id_function_text()
    operations.execute(DDL(function_text))


@Operations.implementation_for(DropNextBigIntegerIdFunctionOp)
def drop_next_bigint_id_function(operations, operation):
    operations.execute('drop function next_bigint_id')


@renderers.dispatch_for(CreateNextBigIntegerIdFunctionOp)
def render_create_next_bigint_id_function(autogen_context, op):
    return "op.create_next_bigint_id_function()"


@renderers.dispatch_for(DropNextBigIntegerIdFunctionOp)
def render_drop_next_bigint_id_function(autogen_context, op):
    return "op.drop_next_bigint_id_function()"


@comparators.dispatch_for("schema")
def compare_sequences(autogen_context, upgrade_ops, schemas):
    """
    Insert operation to create next_bigint_id function for the very first migration
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
        next_bigint_id_op = CreateNextBigIntegerIdFunctionOp()
        upgrade_ops.ops.insert(0, next_bigint_id_op)
