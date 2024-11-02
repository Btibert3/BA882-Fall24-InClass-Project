from google.cloud import storage

import os
import pandas as pd
import joblib
import logging

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score

logging.basicConfig(level=logging.INFO)

# Load environment variables for GCP
project_id = os.getenv('GCP_PROJECT', 'btibert-ba882-fall24')
gcp_region = os.getenv('GCP_REGION', 'us-central1')
bucket_name = os.getenv('GCS_BUCKET', 'btibert-ba882-fall24-vertex-models')
training_data_path = os.getenv('TRAINING_DATA_PATH', 'training-data/post-length/post-length.csv')
model_output_path = os.getenv('MODEL_OUTPUT_PATH', 'models/post-length/')

# Function to load CSV from GCS
def load_data_from_gcs(bucket_name, file_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.download_to_filename('/tmp/data.csv')
    return pd.read_csv('/tmp/data.csv')


