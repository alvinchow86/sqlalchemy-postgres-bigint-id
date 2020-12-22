from sqlalchemy_bigint_id.types import BigIntegerID


def get_bigid_column_from_table(table):
    bigid_column = None

    for column in table.columns:
        if isinstance(column.type, BigIntegerID) and column.primary_key:
            bigid_column = column

    return bigid_column
