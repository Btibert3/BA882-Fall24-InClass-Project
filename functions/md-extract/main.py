############# scaffold the pipeline

# imports
import functions_framework
from google.cloud import secretmanager
from google.cloud import storage
import duckdb
import feedparser
import pandas as pd
import requests
import datetime
import uuid
import json 
from io import BytesIO

@functions_framework.http
def main(request):
    
    # instantiate the services 
    sm = secretmanager.SecretManagerServiceClient()
    storage_client = storage.Client()

    # replace below with your own product settings
    project_id = 'btibert-ba882-fall24'
    secret_id = 'mother_duck'   #<---------- this is the name of the secret your created above!
    version_id = 'latest'
    bucket_name = "btibert882_24_sandbox"
    JOB_ID = datetime.datetime.now().strftime("%Y%m%d%H%M") + "-" + str(uuid.uuid4())

    # setup the bucket
    bucket = storage_client.bucket(bucket_name)

    # some setup that we will use for this task (db and schema names)
    # ideally schema comes in from environment variable but ok for now
    db = 'sandbox'
    schema = "dev"
    db_schema = f"{db}.{schema}"

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = sm.access_secret_version(request={"name": name})
    md_token = response.payload.data.decode("UTF-8")

    # initiate the MotherDuck connection through an access token through
    md = duckdb.connect(f'md:?motherduck_token={md_token}') 

    # lets look at the high level bits
    print(md.sql("SHOW DATABASES").show())


    ######################################################## create the schema for the raw tables

    # define the DDL statement with an f string
    create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db};"  
    print(f"create db sql: {create_db_sql}") 

    # execute the command to create the database
    md.sql(create_db_sql)

    # confirm it exists
    print(md.sql("SHOW DATABASES").show())

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

    ######################################################## light parsing of the feeds

    print("flattening the entries")

    # flatten all the entries
    entries = []
    for feed in feed_list:
        entries.extend(feed.entries)

    entries_parsed = []
    for entry in entries:
        pe = dict(
            id = entry.id,
            title = entry.title,
            link = entry.link,
            summary = entry.summary,
            tags = entry.tags,
            post_source = entry.content[0].get('value'),
            # published_timestamp = datetime.datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z").isoformat(),
            published_timestamp = entry.published,
            job_id = JOB_ID,
        )
        entries_parsed.append(pe)



    # convert to a dataframe
    edf = pd.DataFrame(entries_parsed)
    print(f"converted the entries to a dataframe of shape: {edf.shape}")

    # write to gcs
    blob_name = f"rss/{JOB_ID}/extracted_entries.csv"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(edf.to_csv(index=False), 'text/csv')


    ######################################################## create a raw table to hold the extracted posts

    # cleanup the raw table, this is new for every job
    tbl_raw = "raw_posts"
    raw_table_cleanup= f"""
    DROP TABLE IF EXISTS {db_schema}.{tbl_raw}
    """
    md.sql(raw_table_cleanup)
    print(f"table was dropped: {raw_table_cleanup}")


    # insert the data
    edf['published_timestamp'] = pd.to_datetime(edf['published_timestamp'], utc=True).dt.tz_localize(None)
    edf['ingest_timestamp'] = pd.Timestamp.now()
    raw_insert = f"""
    CREATE TABLE {db_schema}.{tbl_raw} as SELECT * from edf
    """
    md.sql(raw_insert)
    print(f"raw table {tbl_raw} was added") 


    ######################################################## parse tags into motherduck

    # iterrows is not ideal, but with a job getting about 160 entries in a dataframe, this isnt bad
    rows = []
    for _, row in edf.iterrows():
        for entry in row['tags']:
            new_row = entry.copy()  # Copy the dictionary
            new_row['post_id'] = row['id']  # Retain the original id
            new_row['job_id'] = row['job_id']  # Retain the original jobid
            rows.append(new_row)
    tags_df = pd.DataFrame(rows)
    print(f"tags were flatted to shape: {tags_df.shape}") 


    # cleanup the raw table, this is new for every job
    tbl_raw = "raw_tags"
    raw_table_cleanup= f"""
    DROP TABLE IF EXISTS {db_schema}.{tbl_raw}
    """
    md.sql(raw_table_cleanup)


    # insert the data
    tags_df['ingest_timestamp'] = pd.Timestamp.now()
    raw_insert = f"""
    CREATE TABLE {db_schema}.{tbl_raw} as SELECT * FROM tags_df
    """
    md.sql(raw_insert)

    # write to gcs
    blob_name = f"rss/{JOB_ID}/extracted_tags.csv"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(tags_df.to_csv(index=False), 'text/csv')

    ######################################################## return

    return {'statusCode': 200}


