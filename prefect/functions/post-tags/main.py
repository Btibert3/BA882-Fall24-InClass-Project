# create/update a view to associate tags to post content, intended for ML classification

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
ml_dataset_path = '/training-data/post-tags/'

# db setup
db = 'awsblogs'
stage_db_schema = f"{db}.stage"
ml_schema = f"{db}.ml"
ml_view_name = "post_tags"

ingest_timestamp = pd.Timestamp.now()

############################################################### helpers

## define the SQL
ml_view_sql = f"""
CREATE OR REPLACE VIEW {ml_schema}.{ml_view_name} AS
WITH
posts AS (
    SELECT id, content_text
    FROM awsblogs.stage.posts
),

top_tags AS (
    SELECT LOWER(term) AS term, COUNT(*) AS total
    FROM awsblogs.stage.tags
    GROUP BY term
    ORDER BY total DESC
    LIMIT 20
),

tags AS (
    SELECT t.post_id, LOWER(t.term) AS term
    FROM awsblogs.stage.tags t
    INNER JOIN top_tags tt ON LOWER(t.term) = LOWER(tt.term)
)

SELECT
    p.id,
    p.content_text,
    STRING_AGG(LOWER(t.term), ',') AS labels,
    CURRENT_TIMESTAMP AS created_at
FROM posts p
INNER JOIN tags t ON p.id = t.post_id
GROUP BY p.id, p.content_text;
"""

# Helper to check if dataset exists in Vertex AI
def get_existing_dataset(display_name):
    datasets = aiplatform.TabularDataset.list(
        filter=f'display_name="{display_name}"'
    )
    return datasets[0] if datasets else None

############################################################### main task

@functions_framework.http
def task(request):

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
    print("Creating the schema if it doesn't exist and creating/updating the view")
    md.sql(f"CREATE SCHEMA IF NOT EXISTS {ml_schema};")
    md.sql(ml_view_sql)

    # grab the view as a pandas dataframe, just the text and the labels
    df = md.sql(f"SELECT content_text, labels FROM {ml_schema}.{ml_view_name};").df()

    # cleanup for modeling - a list column for use in sklearn
    df['labels'] = df['labels'].apply(lambda x: x.split(','))

    # write the dataset to the training dataset path on GCS
    print("Writing the parquet file to GCS")
    dataset_path = "gcs://" + ml_bucket_name + ml_dataset_path + "post-tags.parquet"
    df.to_parquet(dataset_path)

    # Initialize Vertex AI
    print("Creating or updating the Vertex AI dataset")
    aiplatform.init(project=project_id, location=project_region)
    
    # Check if the dataset already exists
    display_name = "awsblogs-post-tags"
    existing_dataset = get_existing_dataset(display_name)

    if existing_dataset:
        print(f"Dataset '{display_name}' already exists. Updating the dataset...")
        # Import updated data into the existing dataset
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

