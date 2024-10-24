import functions_framework
from google.cloud import secretmanager
import duckdb

@functions_framework.http
def main(request):
    
    # instantiate the services 
    sm = secretmanager.SecretManagerServiceClient()

    # settings
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

    ##################################################### create the schema

    # some setup that we will use for this task (db and schema names)
    db = 'sandbox'
    schema = "dev"
    db_schema = f"{db}.{schema}"

    # define the DDL statement with an f string
    create_db_sql = f"CREATE DATABASE IF NOT EXISTS {db};"   

    # execute the command to create the database
    md.sql(create_db_sql)

    # confirm it exists
    print(md.sql("SHOW DATABASES").show())

    # create the schema
    md.sql(f"CREATE SCHEMA IF NOT EXISTS {db_schema};") 

    ##################################################### create the core tables

    