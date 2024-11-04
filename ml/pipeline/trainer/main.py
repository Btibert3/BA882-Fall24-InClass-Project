##################################################### imports

import functions_framework

import os
import pandas as pd 
import joblib
import uuid
import datetime

from gcsfs import GCSFileSystem

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score

from google.cloud import secretmanager
from google.cloud import storage
import duckdb


# db setup
db = 'awsblogs'
schema = "mlops"
db_schema = f"{db}.{schema}"

# settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'
gcp_region = 'us-central1'


##################################################### helpers

def load_sql(p):
    with open(p, "r") as f:
        sql = f.read()
        return sql

##################################################### task


@functions_framework.http
def task(request):
    "Using Cloud Functions as our compute layer - train models in a pipeline"

    # job_id
    job_id = datetime.datetime.now().strftime("%Y%m%d%H%M") + "-" + str(uuid.uuid4())

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

    # the dataset
    sql = load_sql("dataset.sql")
    df = md.sql(sql).df()

    # Parse incoming request to get parameters (if any)
    try:
        request_json = request.get_json()
    except Exception:
        request_json = {}

    # Model parameters with default values
    max_features = request_json.get('max_features', 5000)
    ngram_range = tuple(request_json.get('ngram_range', (1, 2)))
    model_name = request_json.get('name', 'post length linear regression')

    # Create a pipeline to train the model -- CountVectorizer and then a regression model
    pipeline = Pipeline([
        ('cv', CountVectorizer(max_features=max_features, ngram_range=ngram_range)),
        ('reg', LinearRegression())
    ])

    # Split the dataset
    X_train, X_test, y_train, y_test = train_test_split(df['title'], df['word_count'], test_size=0.2, random_state=882)

    # Fit the model
    pipeline.fit(X_train, y_train)

    # Apply the model
    y_pred = pipeline.predict(X_test)

    # Grab some metrics
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred)

    print(f"r2: {r2}")
    print(f"mae: {mae}")
    print(f"mape: {mape}")

    ############################################# write the model to gcs
    # Write this file to GCS
    GCS_BUCKET = "btibert-ba882-fall24-vertex-models"
    GCS_PATH = f"pipeline/runs/{job_id}"
    FNAME = "model/model.joblib"
    GCS = f"gs://{GCS_BUCKET}/{GCS_PATH}/{FNAME}"

    # Use GCSFileSystem to open a file in GCS
    with GCSFileSystem().open(GCS, 'wb') as f:
        joblib.dump(pipeline, f)
    
    ############################################# write the data to the mlops schema
    insert_query = f"""
    INSERT INTO {db_schema}.model_runs (job_id, name, gcs_path)
    VALUES ('{job_id}', '{model_name}', '{ GCS_BUCKET + "/" + GCS_PATH}');
    """
    print(f"mlops to warehouse: {insert_query}")
    md.sql(insert_query)

    # job metrics
    ingest_timestamp = pd.Timestamp.now()
    metrics = {
      'job_id': job_id,
      'r2': r2,
      'mae': mae,
      'mape': mape,
      'created_at': ingest_timestamp
    }
    metrics_df = pd.DataFrame([metrics])
    metrics_df = pd.melt(metrics_df, 
                    id_vars=['job_id', 'created_at'], 
                    value_vars=['r2', 'mae', 'mape'], 
                    var_name='metric_name', 
                    value_name='metric_value')
    metrics_df = metrics_df[['job_id', 'metric_name', 'metric_value', 'created_at']]
    ingest_sql = f"INSERT INTO {db_schema}.job_metrics SELECT * from metrics_df"
    print(f"mlops to warehouse: {ingest_sql}")
    md.sql(ingest_sql)

    # job params
    params = {
      "max_features": max_features,
      "ngram_range": ngram_range,
      "model": 'LinearRegression',
      'created_at': ingest_timestamp,
      'job_id': job_id
    }
    params_df = pd.DataFrame([params])
    params_df = pd.melt(params_df, 
                id_vars=['job_id', 'created_at'], 
                var_name='parameter_name', 
                value_name='parameter_value')
    params_df = params_df[['job_id', 'parameter_name', 'parameter_value', 'created_at']]
    ingest_sql = f"INSERT INTO {db_schema}.job_parameters SELECT * from params_df"
    print(f"mlops to warehouse: {ingest_sql}")
    md.sql(ingest_sql)

  
    # Return data
    return_data = {
        'r2': r2,
        'mae': mae,
        'mape': mape,
        "model_path": GCS,
        "job_id": job_id,
        "parameters": {
            "max_features": max_features,
            "ngram_range": ngram_range
        }
    }

    return return_data, 200
