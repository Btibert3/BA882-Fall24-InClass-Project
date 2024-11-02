# imports
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

# Save the model to GCS
def save_model_to_gcs(model, bucket_name, model_output_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Save the model locally in the container
    model_filename = 'model.joblib'
    model_path = os.path.join('/tmp', model_filename)
    joblib.dump(model, model_path)

    # Upload the model to GCS 
    blob = bucket.blob(os.path.join(model_output_path, model_filename))
    blob.upload_from_filename(model_path)
    return os.path.join('gs://', bucket_name, model_output_path, model_filename)

logging.info("Loading data from GCS...")
df = load_data_from_gcs(bucket_name, training_data_path)

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

logging.info("Saving the model to GCS...")
model_uri = save_model_to_gcs(pipeline, bucket_name, model_output_path)
print(f"Model saved to: {model_uri}")

# the scikit learn version
import sklearn 
print(f"scikit-learn version: {sklearn.__version__}")