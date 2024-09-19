############# scaffold the pipeline

# imports
from google.cloud import secretmanager
import duckdb
import feedparser
import pandas as pd
import requests
import datetime

# instantiate the service
sm = secretmanager.SecretManagerServiceClient()

# replace below with your own product settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret your created above!
version_id = 'latest'

# Build the resource name of the secret version
name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

# Access the secret version
response = sm.access_secret_version(request={"name": name})
md_token = response.payload.data.decode("UTF-8")

# initiate the MotherDuck connection through an access token through
md = duckdb.connect(f'md:?motherduck_token={md_token}') 

# lets look at the high level bits
md.sql("SHOW DATABASES").show()



######################################################## create the sandbox

# some setup that we will use for this task (db and schema names)
db = 'sandbox'
schema = "dev"
db_schema = f"{db}.{schema}"

# define the DDL statement with an f string
create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db};"   

# execute the command to create the database
md.sql(create_db_sql)

# confirm it exists
md.sql("SHOW DATABASES").show()

# create the schema
md.sql(f"CREATE SCHEMA IF NOT EXISTS {db_schema};")


######################################################## grab the feeds

feeds = [
    'https://aws.amazon.com/blogs/big-data/feed/',
    'https://aws.amazon.com/blogs/compute/feed/',
    'https://aws.amazon.com/blogs/database/feed/',
    'https://aws.amazon.com/blogs/machine-learning/feed/',
    'https://aws.amazon.com/blogs/containers/feed/',
    'https://aws.amazon.com/blogs/infrastructure-and-automation/feed/',
    'https://aws.amazon.com/blogs/aws/feed/',
    'https://aws.amazon.com/blogs/business-intelligence/feed/',
    'https://aws.amazon.com/blogs/storage/feed/'
]

feed_list = []
for feed in feeds:
    try:
        r = requests.get(feed)
        feed = feedparser.parse(r.content)
        print(feed.feed.title)
        feed_list.append(feed)
    except Exception as e:
        print(e)

# flatten all the entries
entries = []
for feed in feed_list:
    entries.extend(feed.entries)

# list of dictionaries as we are just being methodical step by step
entry_data = []
for entry in entries:
    entry_data.append(dict(entry))


######################################################## ensure no dupes

# the entries from the feeds
entries = pd.DataFrame(entry_data)

# drop dupes here
entries_nodupes = entries.drop_duplicates(subset=['link'])


######################################################## create a raw table to hold

# cleanup the raw table, this is new for every job
tbl_raw = "raw_posts"
raw_table_cleanup= f"""
DROP TABLE IF EXISTS {db_schema}.{tbl_raw}
"""
md.sql(raw_table_cleanup)

# insert directly into the raw table

raw_insert = f"""
CREATE TABLE {db_schema}.{tbl_raw} as SELECT * from entries_nodupes
"""
entries_nodupes['ingest_timestamp'] = pd.Timestamp.now()
md.sql(raw_insert)


## do some light parsing before above