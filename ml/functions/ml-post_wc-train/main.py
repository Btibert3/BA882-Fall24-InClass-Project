##################################################### imports

import functions_framework

import os
import pandas as pd 
import joblib

from gcsfs import GCSFileSystem

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score

from google.cloud import storage
from google.cloud import aiplatform


##################################################### settings

# settings
project_id = 'btibert-ba882-fall24'  # <------- change this to your value
project_region = 'us-central1' # 


##################################################### task


@functions_framework.http
def task(request):
  "Fit the model using a cloud function"

  # we are harcoding the dataset -- why might this not be a great idea?
  GCS_PATH = "gs://btibert-ba882-fall24-vertex-models/training-data/post-length/post-length.parquet"
  
  # get the dataset
  df = pd.read_parquet(GCS_PATH)
  print(df.head())

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
  GCS_PATH = "models/post-length/"
  FNAME = "model.joblib"
  GCS = f"gs://{GCS_BUCKET}/{GCS_PATH}{FNAME}"

  # Use GCSFileSystem to open a file in GCS
  with GCSFileSystem().open(GCS, 'wb') as f:
      joblib.dump(pipeline, f)
  
  return_data = {
    'r2': r2, 
    'mae': mae, 
    'mape': mape, 
    "model_path": GCS
  }

  return return_data, 200


