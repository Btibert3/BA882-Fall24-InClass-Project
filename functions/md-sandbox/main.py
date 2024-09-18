# a sandbox script to connect MD and GCP
# document learnings here

# access the secret, the token stored in GCP secrets
# as the runtime is on gcp (cloud scheduler, workflow, cloud functions, storage)
# might make sense especially for vector db anyway

# imports
from google.cloud import secretmanager
import duckdb
import feedparser
import pandas as pd

################################################# secrets

sm = secretmanager.SecretManagerServiceClient()

project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'
version_id = 'latest'


# Build the resource name of the secret version
name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

# Access the secret version
response = sm.access_secret_version(request={"name": name})
md_token = response.payload.data.decode("UTF-8")


################################################# connect to md and poke around


# initiate the MotherDuck connection through an access token through
md = duckdb.connect(f'md:?motherduck_token={md_token}') 

# lets look at the high level bits
md.sql("SHOW DATABASES").show()

# some simple things -- may need to refresh (browser) no button on the UI explicit
db = 'aws_blogs'
schema = "sandbox"
create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db};"   # main is created for us
md.sql(create_db_sql)
md.sql("SHOW DATABASES").show()

# for this task
db_schema = f"{db}.{schema}"

md.sql(f"CREATE SCHEMA IF NOT EXISTS {db_schema};")


# create some tables in the database, not not using, just naming convention
# https://duckdb.org/docs/sql/statements/create_table.html
table_create_sql = f"""
CREATE TABLE IF NOT EXISTS {db_schema}.users  (
    user_id INTEGER PRIMARY KEY,  -- Primary key
    username VARCHAR,             -- Username field
    email VARCHAR,                -- Email field
    created_at TIMESTAMP          -- Timestamp when the user was created
);
"""
md.sql(table_create_sql)

####### uses main schema, I didnt create one nor use, ok for now
### main schema
## MD ui is nice, shows types


md.sql("DROP DATABASE aws_blogs;")

md.close()


################################################# sandbox above, now replicate GCP flow

# initiate the MotherDuck connection through an access token through
md = duckdb.connect(f'md:?motherduck_token={md_token}') 

# lets look at the high level bits
md.sql("SHOW DATABASES").show()

# some simple things -- may need to refresh (browser) no button on the UI explicit
db = 'aws_blogs'
create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db};"   # main is created for us
md.sql(create_db_sql)
md.sql("SHOW DATABASES").show()

# the schema -- hopefully from env vars
schema = "sandbox"
db_schema = f"{db}.{schema}"
md.sql(f"CREATE SCHEMA IF NOT EXISTS {db_schema};")

# create the posts table
create_posts_sql = f"""
CREATE TABLE IF NOT EXISTS {db_schema}.post(
        id STRING,
        url STRING,
        title STRING,
        published_date TIMESTAMP,
        content STRING,
        summary STRING,
        ingest_timestamp TIMESTAMP,
        job_id STRING,
        raw_feed STRING
);
"""
md.sql(create_posts_sql)


################################################# another schema to simulate moving data
## from function to gcs to md

# initiate the MotherDuck connection through an access token through
md = duckdb.connect(f'md:?motherduck_token={md_token}') 

# lets look at the high level bits
md.sql("SHOW DATABASES").show()

# some simple things -- may need to refresh (browser) no button on the UI explicit
db = 'ba882'
schema = "sandbox"
create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db};"   # main is created for us
md.sql(create_db_sql)
md.sql("SHOW DATABASES").show()

# for this task
db_schema = f"{db}.{schema}"

md.sql(f"CREATE SCHEMA IF NOT EXISTS {db_schema};")

# grab a feed
url = 'https://aws.amazon.com/blogs/big-data/feed/'

# Parse the RSS feed
feed = feedparser.parse(url)

# flatten
entries = []
for entry in feed.entries:
    # Convert each entry to a dictionary and flatten it
    entry_dict = {key: entry[key] for key in entry.keys()}
    entries.append(entry_dict)

# Step 3: Convert the list of dictionaries into a Pandas DataFrame
df = pd.DataFrame(entries)

# write this to a table - A TEST, DOES IT REALLY WORK?
md.execute(f"CREATE TABLE {db_schema}.rss_feed AS SELECT * FROM df;")

# above shows how awesome duckdb/md are
df.info()
md.execute(f"DESCRIBE TABLE {db_schema}.rss_feed").df()

# -----> this could highlight concepts of EtLT, or ELT, where just throw it in, and work
# patterns in the data allow us to be less flexible early on, 
# also, could think about the idea of just loading into the db and parsing

# create a table like the other
md.execute(f"CREATE TABLE {db_schema}.rss_feed_tmp AS FROM {db_schema}.rss_feed LIMIT 0;")

# copy into
md.execute(f"INSERT INTO {db_schema}.rss_feed_tmp SELECT * from {db_schema}.rss_feed;")