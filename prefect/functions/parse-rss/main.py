import functions_framework
from google.cloud import secretmanager
from google.cloud import storage
import duckdb
import json
import pandas as pd

# settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'
bucket_name = 'btibert-ba882-fall24-awsblogs'


# db setup
db = 'awsblogs'
schema = "raw"
db_schema = f"{db}.{schema}"


# tmp = {"blob_name":"jobs/202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f/extracted_entries.json","bucket_name":"btibert-ba882-fall24-awsblogs","job_id":"202409211821-b20feead-0dc0-431e-9f85-479e6ca8a33f","num_entries":160}

############################################## main task

@functions_framework.http
def task(request):

    # Parse the request data
    request_json = request.get_json(silent=True)
    print(f"request: {json.dumps(request_json)}")

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
    create_schema = f"CREATE SCHEMA IF NOT EXISTS {db_schema}"
    md.sql(create_schema)

    ########################### get the file that triggered this post

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




