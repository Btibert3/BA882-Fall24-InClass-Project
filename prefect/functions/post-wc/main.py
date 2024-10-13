# create/update a view to associate content length to the title for a regression task

import functions_framework
from google.cloud import secretmanager
from google.cloud import storage
from google.cloud import aiplatform
import duckdb
import pandas as pd
import datetime

# settings
project_id = 'btibert-ba882-fall24'
project_region = 'us-central1'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'
bucket_name = 'btibert-ba882-fall24-awsblogs'
ml_bucket_name = 'btibert-ba882-fall24-vertex-models'
ml_dataset_path = '/training-data/post-length/'

# db setup
db = 'awsblogs'
stage_db_schema = f"{db}.stage"
ml_schema = f"{db}.ml"
ml_view_name = "post_length"

############################################################### helpers

## define the SQL
ml_view_sql = f"""
CREATE OR REPLACE VIEW {ml_schema}.{ml_view_name} 
AS
select 
    title, 
    array_length(regexp_split_to_array(content_text, '\\s+')) AS word_count,
    CURRENT_TIMESTAMP AS created_at
from {stage_db_schema}.posts;
"""

# Helper to check if dataset exists
def get_existing_dataset(display_name):
    # Search for datasets with the given display name
    datasets = aiplatform.TabularDataset.list(
        filter=f'display_name="{display_name}"'
    )
    
    # Return the first dataset found with the matching display name, if any
    return datasets[0] if datasets else None

############################################################### main task

@functions_framework.http
def task(request):

    # we will not be passing in any data into the request

    # instantiate the services 
    sm = secretmanager.SecretManagerServiceClient()
    storage_client = storage.Client()

    # connect to Motherduck, the cloud data warehouse
    print("connecting to Motherduck")
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = sm.access_secret_version(request={"name": name})
    md_token = response.payload.data.decode("UTF-8")
    md = duckdb.connect(f'md:?motherduck_token={md_token}') 

    # create the view
    print("creating the schema if it doesn't exist and creating/updating the view")
    md.sql(f"CREATE SCHEMA IF NOT EXISTS {ml_schema};")
    md.sql(ml_view_sql)

    # grab the view as a pandas dataframe, just the text and the labels
    df = md.sql(f"select title, word_count from {ml_schema}.{ml_view_name};").df()

    # write the dataset to the training dataset path on GCS
    print("writing the parquet file to GCS")
    dataset_path = "gcs://" + ml_bucket_name + ml_dataset_path + "post-length.parquet"
    df.to_parquet(dataset_path)

    # register the dataset on VertexAI
    print("creating or updating the Vertex AI dataset")
    aiplatform.init(project=project_id, location=project_region)
    
    # Check if dataset already exists
    display_name = "awsblogs-post-length"
    existing_dataset = get_existing_dataset(display_name)
    
    if existing_dataset:
        print(f"Dataset '{display_name}' already exists. Updating the dataset...")
        # Import new data to the existing dataset
        existing_dataset.import_data(gcs_source=dataset_path.replace("gcs", "gs"))
        print(f"Dataset '{display_name}' updated successfully.")
    else:
        print(f"Creating new dataset '{display_name}' on Vertex AI...")
        dataset = aiplatform.TabularDataset.create(
            display_name=display_name,
            gcs_source=dataset_path.replace("gcs", "gs"),
            sync=True
        )
        print(f"Dataset '{display_name}' created successfully.")

    return {"dataset_path": dataset_path}, 200
