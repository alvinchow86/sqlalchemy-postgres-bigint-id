from sqlalchemy_bigint_id.types import BigIntegerID


def get_bigint_id_column_from_table(table):
    bigint_id_column = None

    for column in table.columns:
        if isinstance(column.type, BigIntegerID) and column.primary_key:
            bigint_id_column = column

    return bigint_id_column
