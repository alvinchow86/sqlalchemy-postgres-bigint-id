from sqlalchemy import types


class BigID(types.TypeDecorator):
    """
    Wrapper for a BigInteger primary key that we want to use the nextbigid() function on
    We just make a separate class to make this explicit and to let the migration scripts
    """
    impl = types.BigInteger
