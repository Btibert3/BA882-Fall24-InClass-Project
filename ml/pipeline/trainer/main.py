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
schema = "ml"
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


    # create a pipeline to train the model -- tfidf and then a regression model
    pipeline = Pipeline([
        ('tfidf', CountVectorizer(max_features=5000, ngram_range=(1,2))),
        ('reg', LinearRegression())
    ])

    # split the dataset
    X_train, X_test, y_train, y_test = train_test_split(df['title'], df['word_count'], test_size=0.2, random_state=882)

    # fit the model
    pipeline.fit(X_train, y_train)

    # apply the model
    y_pred = pipeline.predict(X_test)

    # grab some metrics
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred)

    print(f"r2: {r2}")
    print(f"mae: {mae}")
    print(f"mape: {mape}")

    # write this file to gcs
    GCS_BUCKET = "btibert-ba882-fall24-vertex-models"
    GCS_PATH = f"pipeline/runs/{job_id}/model"
    FNAME = "model.joblib"
    GCS = f"gs://{GCS_BUCKET}/{GCS_PATH}/{FNAME}"

    # Use GCSFileSystem to open a file in GCS
    with GCSFileSystem().open(GCS, 'wb') as f:
        joblib.dump(pipeline, f)
    
    ########################### write the data to mother duck

    return_data = {
      'r2': r2, 
      'mae': mae, 
      'mape': mape, 
      "model_path": GCS
    }

    return return_data, 200


