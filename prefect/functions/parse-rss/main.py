import functions_framework
from google.cloud import secretmanager
from google.cloud import storage
import duckdb
import json
import pandas as pd
import datetime
from bs4 import BeautifulSoup
import html

# settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'
bucket_name = 'btibert-ba882-fall24-awsblogs'


# db setup
db = 'awsblogs'
schema = "raw"
db_schema = f"{db}.{schema}"
ingest_timestamp = pd.Timestamp.now()


############################################################### helpers

def parse_published(date_str):
    dt_with_tz = datetime.datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
    dt_naive = dt_with_tz.replace(tzinfo=None)
    timestamp = pd.Timestamp(dt_naive)
    return timestamp

def extract_content_source(content):
    raw_value = content[0].get('value')
    return raw_value


def extract_content_text(content):
    soup = BeautifulSoup(content, 'html.parser')
    cleaned_text = html.unescape(soup.get_text())
    return cleaned_text


def extract_image_data(html_content, post_id):
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img')
    
    for i,img in enumerate(images):
        image_data = {
            'post_id': post_id,
            'index': i,
            'src': img.get('src'),
            'width': img.get('width'),
            'height': img.get('height'),

        }
        image_info.append(image_data)

############################################################### main task


@functions_framework.http
def task(request):

    # Parse the request data
    request_json = request.get_json(silent=True)
    print(f"request: {json.dumps(request_json)}")

    # TODO: DELETE THIS: awful, but start with this
    request_json = {
        "blob_name":"jobs/202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f/extracted_entries.json",
        "bucket_name":"btibert-ba882-fall24-awsblogs",
        "job_id":"202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f",
        "num_entries":160}

    # get the jobid
    job_id = request_json.get('job_id')

    # instantiate the services 
    sm = secretmanager.SecretManagerServiceClient()
    storage_client = storage.Client()

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = sm.access_secret_version(request={"name": name})
    md_token = response.payload.data.decode("UTF-8")

    # initiate the MotherDuck connection through an access token through
    md = duckdb.connect(f'md:?motherduck_token={md_token}') 

    # create the raw schema if it doesnt exist
    create_schema = f"DROP SCHEMA IF EXISTS {db_schema} CASCADE; CREATE SCHEMA IF NOT EXISTS {db_schema};"
    md.sql(create_schema)

    ############################################################### get the file that triggered this post

    # Access the 'id' from the incoming request
    bucket_name = request_json.get('bucket_name')
    file_path = request_json.get('blob_name')
    print(f"bucket: {bucket_name} and blob name {file_path}")

    # get the file
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    json_data = blob.download_as_string()
    entries = json.loads(json_data)
    print(f"retrieved {len(entries)} entries")

    # make it a dataframe
    entries_df = pd.DataFrame(entries)
    entries_df['job_id'] = job_id

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: tags

    # iterrows is not ideal, but with a job getting about 160 entries in a dataframe, this isnt bad
    tag_rows = []
    for _, row in entries_df.iterrows():
        for entry in row['tags']:
            new_row = entry.copy()  # Copy the dictionary
            new_row['post_id'] = row['id']  # Retain the original id
            new_row['job_id'] = row['job_id']  # Retain the original jobid
            tag_rows.append(new_row)
    tags_df = pd.DataFrame(tag_rows) 
    tags_df = tags_df[['term', 'post_id', 'job_id']]  # a couple keys always appear blank
    tags_df['ingestion_timestamp'] = ingest_timestamp
    print(f"tags were flatted to shape: {tags_df.shape}") 

    # table sql
    raw_tbl_name = f"{db_schema}.tags"
    raw_tbl_sql = f"""
    DROP TABLE IF EXISTS {raw_tbl_name} ;
    CREATE TABLE {raw_tbl_name} (
        term VARCHAR
        ,post_id VARCHAR
        ,job_id VARCHAR
        ,ingestion_timestamp TIMESTAMP 
    );
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # ingest
    md.sql(f"INSERT INTO {raw_tbl_name} SELECT * from tags_df")
    print(f"rows added to {raw_tbl_name}")


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: posts

    # copy the object
    posts_df = entries_df.copy()

    # some light transforms on datetimes for post timestamp and ingestion
    posts_df['published'] = posts_df['published'].apply(parse_published)
    posts_df['ingest_timestamp'] = pd.Timestamp.now()

    # the content isolated
    posts_df['content_source'] = posts_df['content'].apply(extract_content_source)
    posts_df['content_text'] = posts_df['content_source'].apply(extract_content_text)

    # keep the columns we want, some data loss but we are ok with that
    keep_cols = [
        'id', 
        'link', 
        'title',  
        'summary', 
        'content_source',
        'content_text', 
        'job_id',
        'published', 
        'ingest_timestamp', 
    ]
    posts_df = posts_df[keep_cols]

    # table sql
    raw_tbl_name = f"{db_schema}.posts"
    raw_tbl_sql = f"""
    DROP TABLE IF EXISTS {raw_tbl_name} ;
    CREATE TABLE {raw_tbl_name} (
        id VARCHAR PRIMARY KEY
        ,link VARCHAR
        ,title VARCHAR
        ,summary VARCHAR
        ,content_source VARCHAR
        ,content_text VARCHAR
        ,job_id VARCHAR
        ,published TIMESTAMP 
        ,ingest_timestamp TIMESTAMP
    );
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # ingest
    md.sql(f"INSERT INTO {raw_tbl_name} SELECT * from posts_df")
    print(f"rows added to {raw_tbl_name}")



    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: images
    # NOTE: may not need a mapping table, just store the data repeated

    # apply the function to each row in the DataFrame
    image_info = []
    for index, row in posts_df.iterrows():
        extract_image_data(row['content_source'], row['id'])
    
    # flatten into a dataframe
    images_df = pd.DataFrame(image_info)

    # light cleanup - a handful may not have dimensions
    images_df = images_df.dropna(subset="src")
    images_df['width'] = pd.to_numeric(images_df['width'], errors='coerce')
    images_df['height'] = pd.to_numeric(images_df['height'], errors='coerce')



    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: embedded links


    
    






    ########################### return

    return {}, 200










    




