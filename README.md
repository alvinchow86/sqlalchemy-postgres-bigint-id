# SQLAlchemy Postgres Big Id

This is a library for making it easy to generate 64-bit BIGINT ids for Postgres tables in SQLAlchemy and Alembic. Note that this documentation is targeted for  SQLAlchemy ORM users, but it should also work for general usage. This library will dub this 64-big BIGINT type with special generation "BigID", as this is most likely to be useful for primary IDs.

Install this library once, and never worry about running out of IDs or painful ID type migrations ever again in your application! 

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

### 1. Set up custom epoch time
You will need to decide on some "epoch" time. Just choose some time that is earlier than any tables have been created in your system or your organization has been formed. I would choose something at the beginning of the year or something for simplicy. Then run `sqlalchemy_bigid.configure()` early in your application. You don't need to define it earlier than you need to, so you can maximize the number of usable years.

This epoch time should be set and defined once, and never changed again.

Add this code something in your application initial setup.
```python
BIGID_EPOCH_SECONDS = 1589674264    # this is 1/1/2020

sqlalchemy_bigid.configure(epoch_seconds=BIGID_EPOCH_SECONDS)
```

### 2. Register postgres functions
Call `sqlalchemy_bigid.register_postgres_functions()` with your `Base.metadata`. A good place to do this is whereever you are doing your initial SQLAlchemy database setup and engine/session creation.
```python
from sqlalchemy_bigid import register_nextbigid_function

Base = declarative_base()
register_postgres_functions(metadata=Base.metadata)
```

Note that this really only matters when you are doing something like `Base.metadata.create_all(engine)`, which you likely will only do for local dev and testing

### 3. Set up Alembic
In your `alembic/env.py` file add these lines

Somewhere at the top add this, we need this import just to make sure some code is registered
```python
from sqlalchemy_bigid import migration    # noqa make sure custom hooks are registered
```

Edit your `run_migrations_online()` function to something like this

```
def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from sqlalchemy_bigid.migration import writer
    engine = get_engine()

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=writer,
        )

        with context.begin_transaction():
            context.run_migrations()
```

That's it for the one-time setup!

Now in your SQLAlchemy ORM definitions, just use the custom BigID type. It is identical to the `BigInteger` type, but doing this allows this library to detect cases where you want to register it with the Big ID postgres generation function.

```
from sqlalchemy_bigid.types import BigID

class Foo(Base):
    __tablename__ = 'foo'
    id = Column(BigID, primary_key=True)
    ...
```

## How it Works
We first create a Postgres function, called `nextbigid()`. It's generated in this Python script. Note that one hardcoded value is the epoch time, which must be set to something. 

The function itself takes one argument, which is the name of the sequence for your table. This is an improvement over the function in existing articles I've seen, in that we can reuse one Postgres function instead of writing a new one for every table.

```
 create_nextbigid_function_text = f"""
     CREATE OR REPLACE FUNCTION nextbigid(seq_name text, OUT result bigint) AS $$
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
```

Your "initial" migration will have this at the top, which generates the "nextbigid" function via a custom Alembic hook
```python
def upgrade():
   op.create_nextbigid_function()
   ...
```

For any new tables, the library adds a custom `op.execute()` statement that alters the column to use the nextbigid() postgres function for thr default value.

```python
def upgrade():
   op.create_table('foo', 
     ...
   )
   op.execute("ALTER TABLE foo ALTER COLUMN id set default nextbigid('foo_id_seq')")
```

## Future Improvements
- Make the bit allocations customizable (right now I chose 10 bits for sequence, 10 bits for shard, and the rest for timestamp), which is similar to the Instagram scheme but with slight modification.
- This library doesn't take into account sharding, right now it's intended more to bootstrap your tables with the possibility of future sharding. Will rethink this more later, but it's possible that by time you get to that point you may need to do things more manually.

[![CircleCI](https://circleci.com/gh/alvinchow86/sqlalchemy-postgres-bigid.svg?style=svg)](https://circleci.com/gh/alvinchow86/sqlalchemy-postgres-bigid)
