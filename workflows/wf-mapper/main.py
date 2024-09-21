# imports
import functions_framework
import duckdb
import pandas as pd
from google.cloud import secretmanager
import json


@functions_framework.http
def main(request):

    # Parse the request data
    request_json = request.get_json(silent=True)
    print(f"request: {json.dumps(request_json)}")
    
    # Access the 'id' from the incoming request
    if request_json and 'id' in request_json:
        id_to_process = request_json['id']
    else:
        return 'No ID provided', 400
    print(f"processing id {id_to_process}")
    
    # instantiate the services 
    sm = secretmanager.SecretManagerServiceClient()

    # replace below with your own product settings
    project_id = 'btibert-ba882-fall24'
    secret_id = 'mother_duck'   #<---------- this is the name of the secret your created above!
    version_id = 'latest'

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

    # get the record
    sql = f"select * from {db}.{schema}.raw_posts where id = '409b79b6115c8d051434bfcecf60f69c9f2965e0'; "
    post_raw = md.sql(sql)

    print(f"shape is: {post_raw.shape}")

    return {"statusCode":200}
