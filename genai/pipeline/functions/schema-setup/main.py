import functions_framework
from google.cloud import secretmanager
import duckdb

# settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'

# db setup
db = 'awsblogs'
schema = "genai"
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

    # create the schema
    md.sql(f"CREATE SCHEMA IF NOT EXISTS {db_schema};") 

    ##################################################### create the tables

    ## recommended: either a new schema, or a naming convention assuming the # of indexes managed is only a handful at most

    # posts - flag when the records were preocessed
    raw_tbl_name = f"{db_schema}.pinecone_posts"
    raw_tbl_sql = f"""
    CREATE TABLE IF NOT EXISTS {raw_tbl_name} (
        id VARCHAR PRIMARY KEY,
        parsed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    print(f"{raw_tbl_sql}")
    md.sql(raw_tbl_sql)

    
    ## wrap up
    return {}, 200

