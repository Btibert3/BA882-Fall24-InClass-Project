# imports
import functions_framework
from google.cloud import secretmanager
from google.cloud import storage
import json
import duckdb
import pandas as pd

# setup
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'


# db setup
db = 'awsblogs'
schema = "raw"
raw_db_schema = f"{db}.{schema}"
stage_db_schema = f"{db}.stage"


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

# drop if exists and create the raw schema for 
create_schema = f"DROP SCHEMA IF EXISTS {raw_db_schema} CASCADE; CREATE SCHEMA IF NOT EXISTS {raw_db_schema};"
md.sql(create_schema)


############################################################### main task

@functions_framework.http
def task(request):

    # for testing
    # request_json = {
    #     "authors":"gs://btibert-ba882-fall24-awsblogs/jobs/202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f/authors.parquet",
    #     "images":"gs://btibert-ba882-fall24-awsblogs/jobs/202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f/images.parquet",
    #     "links":"gs://btibert-ba882-fall24-awsblogs/jobs/202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f/links.parquet",
    #     "posts":"gs://btibert-ba882-fall24-awsblogs/jobs/202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f/posts.parquet",
    #     "tags":"gs://btibert-ba882-fall24-awsblogs/jobs/202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f/tags.parquet"
    # }

    # Parse the request data
    request_json = request.get_json(silent=True)
    print(f"request: {json.dumps(request_json)}")


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: posts

    # read in from gcs
    posts_path = request_json.get('posts')
    posts_df = pd.read_parquet(posts_path)

    # table logic
    raw_tbl_name = f"{raw_db_schema}.posts"
    raw_tbl_sql = f"""
    DROP TABLE IF EXISTS {raw_tbl_name} ;
    CREATE TABLE {raw_tbl_name} AS SELECT * FROM {stage_db_schema}.posts WHERE FALSE;
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # ingest into raw schema
    ingest_sql = f"INSERT INTO {raw_tbl_name} SELECT * FROM posts_df"
    print(f"Import statement: {ingest_sql}")
    md.sql(ingest_sql)

    # upsert like operation -- will only insert new records, not update
    upsert_sql = f"""
    INSERT INTO {stage_db_schema}.posts AS stage
    SELECT *
    FROM {raw_tbl_name} AS raw
    ON CONFLICT (id)
    DO NOTHING;
    """
    print(upsert_sql)
    md.sql(upsert_sql)
    
    
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: tags

    # read in from gcs
    tags_path = request_json.get('tags')
    tags_df = pd.read_parquet(tags_path)

    # table logic
    raw_tbl_name = f"{raw_db_schema}.tags"
    raw_tbl_sql = f"""
    DROP TABLE IF EXISTS {raw_tbl_name} ;
    CREATE TABLE {raw_tbl_name} AS SELECT * FROM {stage_db_schema}.tags WHERE FALSE;
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # ingest into raw schema
    ingest_sql = f"INSERT INTO {raw_tbl_name} SELECT * FROM tags_df"
    print(f"Import statement: {ingest_sql}")
    md.sql(ingest_sql)

    # upsert like operation -- will only insert new records, not update
    upsert_sql = f"""
    INSERT INTO {stage_db_schema}.tags AS stage
    SELECT *
    FROM {raw_tbl_name} AS raw
    ON CONFLICT (term, post_id)
    DO NOTHING;
    """
    print(upsert_sql)
    md.sql(upsert_sql)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: links

    # read in from gcs
    links_path = request_json.get('links')
    links_df = pd.read_parquet(links_path)

    # table logic
    raw_tbl_name = f"{raw_db_schema}.links"
    raw_tbl_sql = f"""
    DROP TABLE IF EXISTS {raw_tbl_name} ;
    CREATE TABLE {raw_tbl_name} AS SELECT * FROM {stage_db_schema}.links WHERE FALSE;
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # ingest into raw schema
    ingest_sql = f"INSERT INTO {raw_tbl_name} SELECT * FROM links_df"
    print(f"Import statement: {ingest_sql}")
    md.sql(ingest_sql)

    # upsert like operation -- will only insert new records, not update
    upsert_sql = f"""
    INSERT INTO {stage_db_schema}.links AS stage
    SELECT *
    FROM {raw_tbl_name} AS raw
    ON CONFLICT (post_id, index, href)
    DO NOTHING;
    """
    print(upsert_sql)
    md.sql(upsert_sql)


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: images

    # read in from gcs
    images_path = request_json.get('images')
    images_df = pd.read_parquet(images_path)
    
    # table logic
    raw_tbl_name = f"{raw_db_schema}.images"
    raw_tbl_sql = f"""
    DROP TABLE IF EXISTS {raw_tbl_name} ;
    CREATE TABLE {raw_tbl_name} AS SELECT * FROM {stage_db_schema}.images WHERE FALSE;
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # ingest into raw schema
    ingest_sql = f"INSERT INTO {raw_tbl_name} SELECT * FROM images_df"
    print(f"Import statement: {ingest_sql}")
    md.sql(ingest_sql)

    # upsert like operation -- will only insert new records, not update
    upsert_sql = f"""
    INSERT INTO {stage_db_schema}.images AS stage
    SELECT *
    FROM {raw_tbl_name} AS raw
    ON CONFLICT (post_id, index, src)
    DO NOTHING;
    """
    print(upsert_sql)
    md.sql(upsert_sql)


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ tbl: authors

    # read in from gcs
    authors_path = request_json.get('authors')
    authors_df = pd.read_parquet(authors_path)

    # table logic
    raw_tbl_name = f"{raw_db_schema}.authors"
    raw_tbl_sql = f"""
    DROP TABLE IF EXISTS {raw_tbl_name} ;
    CREATE TABLE {raw_tbl_name} AS SELECT * FROM {stage_db_schema}.authors WHERE FALSE;
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # ingest into raw schema
    ingest_sql = f"INSERT INTO {raw_tbl_name} SELECT * FROM authors_df"
    print(f"Import statement: {ingest_sql}")
    md.sql(ingest_sql)

    # upsert like operation -- will only insert new records, not update
    upsert_sql = f"""
    INSERT INTO {stage_db_schema}.authors AS stage
    SELECT *
    FROM {raw_tbl_name} AS raw
    ON CONFLICT (post_id, index, name)
    DO NOTHING;
    """
    print(upsert_sql)
    md.sql(upsert_sql)


    return {}, 200

