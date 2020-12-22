from sqlalchemy import DDL, event

from sqlalchemy_bigint_id.utils import get_bigint_id_column_from_table
from sqlalchemy_bigint_id import config


RESERVED_KEYWORDS = (
    'user',
    'check',
)


def get_next_bigint_id_function_text():
    """
    Generate the Postgres function text for the next_bigint_id() function
    """
    epoch_seconds = config.EPOCH_SECONDS
    if epoch_seconds is None:   # pragma: no cover
        raise AssertionError('Please configure EPOCH_SECONDS before using library')

    epoch_milliseconds = epoch_seconds * 1000

    create_next_bigint_id_function_text = f"""
        CREATE OR REPLACE FUNCTION next_bigint_id(seq_name text, OUT result bigint) AS $$
        DECLARE
            our_epoch bigint := {epoch_milliseconds};
            seq_id bigint;
            now_millis bigint;
            shard_id int := 0;
        BEGIN
            SELECT nextval(seq_name) %% 1024 INTO seq_id;

            SELECT FLOOR(EXTRACT(EPOCH FROM clock_timestamp()) * 1000) INTO now_millis;
            result := (now_millis - our_epoch) << 20;
            result := result | (shard_id << 10);
            result := result | (seq_id);
        END;
        $$ LANGUAGE PLPGSQL;
        """
    return create_next_bigint_id_function_text


def get_create_next_bigint_id_function():
    create_next_bigint_id_function_text = get_next_bigint_id_function_text()
    create_next_bigint_id_function = DDL(create_next_bigint_id_function_text)
    return create_next_bigint_id_function


def register_next_bigint_id_function(metadata):
    """
    Create the next_bigint_id function on initial table creation (mostly for dev)
    """
    create_next_bigint_id_function = get_create_next_bigint_id_function()
    event.listen(metadata, 'before_create', create_next_bigint_id_function)


def generate_next_bigint_id_sql_for_table(table):
    """
    If a Table has a BigIntegerId column, return the Alter table SQL to use next_bigint_id()
    """
    bigint_id_column = get_bigint_id_column_from_table(table)
    if bigint_id_column is not None:
        return generate_next_bigint_id_sql(table.name, bigint_id_column.key)


def generate_next_bigint_id_sql(table_name, column_name):
    column = column_name
    table = table_name
    if table_name in RESERVED_KEYWORDS:
        # if using a reserved word, need parentheses
        sql = f"""
ALTER TABLE "{table}" ALTER COLUMN {column} set default next_bigint_id('{table}_{column}_seq')
""".strip()
    else:
        sql = f"ALTER TABLE {table} ALTER COLUMN {column} set default next_bigint_id('{table}_{column}_seq')"
    return sql


def setup_bitint_id_for_all_tables(metadata):
    """
    This is more for Base.create_all() usage than for migrations, but still important for that flow.
    Alembic migrations have a different flow
    """
    tables = metadata.sorted_tables
    for table in tables:
        next_bigint_id_sql = generate_next_bigint_id_sql_for_table(table)
        if next_bigint_id_sql:
            alter_table_bitint_id = DDL(next_bigint_id_sql)
            event.listen(table, 'after_create', alter_table_bitint_id)
