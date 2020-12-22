# SQLAlchemy Postgres Big Id

This is a library for making it easy to generate 64-bit BIGINT ids for Postgres tables in SQLAlchemy and Alembic.

## Features
- Automatically takes care of generating the Postgres function, and sets up columns to use the function as the default value
- Works with both SQLAlchemy table reset functions (for testing/development) and Alembic (migration files are edited to do all the necessary changes)
- Fully tested with 100% unit test coverage

## Background
Instagram published an article on how they generate 64-bit database primary keys a while back (https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c). It is based on the Twitter Snowflake scheme, but without requiing a central server, instead we can just use Postgres functions.

Here are the advantages of this over normal incrementing 32-bit IDs
- Much larger namespace (you will not run out for many many years)
- Does not leak information about the size of your tables

Advantages compared to 128-bit UUID
- Half the space of space compared to UUID. (Note that larger IDs also increase the sizes of indexes and foreign keys)
- Easier to work with and copy-paste/etc, shorter URLS
- Preserve order information (larger IDs are created after small ones)

This scheme also allows for future-proofing in case your application requires sharding later on, as some bits can be dedicated to the shard id.


## How to Use
```
pip install sqlalchemy-postgres-bigid
```

## Hot it Works
Your "initial" migration will have this at the top, which generates the "nextbigid" funciton via a custom Alembic hook
```python
def upgrade():
   op.create_nextbigid_function()
   ...
```

For any new tables, the library adds a custom `op.execute()` statement that alters the column to use the nextbigid() postgres function for thr default value.

```python
def upgrade():
   op.create_table('address', 
     ...
   )
   op.execute("ALTER TABLE address ALTER COLUMN id set default nextbigid('address_id_seq')")
```

[![CircleCI](https://circleci.com/gh/alvinchow86/sqlalchemy-postgres-bigid.svg?style=svg)](https://circleci.com/gh/alvinchow86/sqlalchemy-postgres-bigid)
