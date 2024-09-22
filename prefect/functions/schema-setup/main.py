import functions_framework
from google.cloud import secretmanager
import duckdb

# settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'

# db setup
db = 'awsblogs'
schema = "stage"
db_schema = f"{db}.{schema}"


@functions_framework.http
def task(request):

    # instantiate the services 
    sm = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = sm.access_secret_version(request={"name": name})
    md_token = response.payload.data.decode("UTF-8")

    # initiate the MotherDuck connection through an access token through
    md = duckdb.connect(f'md:?motherduck_token={md_token}') 

    ##################################################### create the schema

    # define the DDL statement with an f string
    create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db};"   

    # execute the command to create the database
    md.sql(create_db_sql)

    # confirm it exists
    print(md.sql("SHOW DATABASES").show())

    # create the schema
    md.sql(f"CREATE SCHEMA IF NOT EXISTS {db_schema};") 

    ##################################################### create the core tables in stage

    # posts
    raw_tbl_name = f"{db_schema}.posts"
    raw_tbl_sql = f"""
    CREATE TABLE IF NOT EXISTS {raw_tbl_name} (
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

    # tags
    raw_tbl_name = f"{db_schema}.tags"
    raw_tbl_sql = f"""
    CREATE TABLE IF NOT EXISTS {raw_tbl_name} (
        term VARCHAR
        ,post_id VARCHAR
        ,job_id VARCHAR
        ,ingest_timestamp TIMESTAMP 
        ,PRIMARY KEY (term, post_id)
    );
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # links
    raw_tbl_name = f"{db_schema}.links"
    raw_tbl_sql = f"""
    CREATE TABLE IF NOT EXISTS {raw_tbl_name} (
        post_id VARCHAR
        ,index INT
        ,href VARCHAR
        ,title VARCHAR
        ,ingest_timestamp TIMESTAMP 
        ,job_id VARCHAR
        ,PRIMARY KEY (post_id, index, href)
    );
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # links
    raw_tbl_name = f"{db_schema}.images"
    raw_tbl_sql = f"""
    CREATE TABLE IF NOT EXISTS {raw_tbl_name} (
        post_id VARCHAR
        ,index INT
        ,src VARCHAR
        ,width INT
        ,height INT
        ,ingest_timestamp TIMESTAMP 
        ,job_id VARCHAR
        ,PRIMARY KEY (post_id, index, src)
    );
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    # authors
    raw_tbl_name = f"{db_schema}.authors"
    raw_tbl_sql = f"""
    CREATE TABLE IF NOT EXISTS {raw_tbl_name} (
        post_id VARCHAR
        ,index INT
        ,name VARCHAR
        ,image VARCHAR
        ,bio VARCHAR
        ,ingest_timestamp TIMESTAMP 
        ,job_id VARCHAR
        ,PRIMARY KEY (post_id, index, name)
    );
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)



    return {}, 200

    