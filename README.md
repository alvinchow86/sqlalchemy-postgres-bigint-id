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

You will need to decide on some "epoch" time. Just choose some time that is earlier than any tables have been created in your system or your organization has been formed. I would choose something at the beginning of the year or something for simplicy. Then run `sqlalchemy_bigid.configure()` early in your application. You don't need to define it earlier than you need to, so you can maximize the number of usable years.

This epoch time should be set and defined once, and never changed again.

Add this code something in your application initial setup.
```python
BIGID_EPOCH_SECONDS = 1589674264    # this is 1/1/2020

sqlalchemy_bigid.configure(epoch_seconds=BIGID_EPOCH_SECONDS)
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

## Future Improvements
- Make the bit allocations customizable (right now I chose 10 bits for sequence, 10 bits for shard, and the rest for timestamp), which is similar to the Instagram scheme but with slight modification.
- This library doesn't take into account sharding, right now it's intended more to bootstrap your tables with the possibility of future sharding. Will rethink this more later, but it's possible that by time you get to that point you may need to do things more manually.

[![CircleCI](https://circleci.com/gh/alvinchow86/sqlalchemy-postgres-bigid.svg?style=svg)](https://circleci.com/gh/alvinchow86/sqlalchemy-postgres-bigid)
