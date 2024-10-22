# imports
from google.cloud import storage

import os
import pandas as pd
import joblib
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score


logging.basicConfig(level=logging.INFO)

# Load environment variables for GCP
project_id = os.getenv('GCP_PROJECT', 'btibert-ba882-fall24')
gcp_region = os.getenv('GCP_REGION', 'us-central1')
bucket_name = os.getenv('GCS_BUCKET', 'btibert-ba882-fall24-vertex-models')
training_data_path = os.getenv('TRAINING_DATA_PATH', 'training-data/post-tags/post-tags.csv')
model_output_path = os.getenv('MODEL_OUTPUT_PATH', 'models/post-tags/')

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

    # Save the model locally
    model_filename = 'model.joblib'
    model_path = os.path.join('/tmp', model_filename)
    joblib.dump(model, model_path)

    # Upload the model to GCS under a "model" subdirectory
    blob = bucket.blob(os.path.join(model_output_path, model_filename))
    blob.upload_from_filename(model_path)
    return os.path.join('gs://', bucket_name, model_output_path, model_filename)

logging.info("Loading data from GCS...")
df = load_data_from_gcs(bucket_name, training_data_path)

# cleanup the labels
logging.info("Cleaning and processing labels...")
df['labels_clean'] = df['labels'].apply(lambda x: x.split(','))

# Convert the labels into a multi-label binary format using MultiLabelBinarizer
mlb = MultiLabelBinarizer()
y = mlb.fit_transform(df['labels_clean'])

# Create a pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=5000)),  # Convert content_text into TF-IDF features
    ('clf', OneVsRestClassifier(LogisticRegression()))  # Train a multi-label classifier
])

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(df['content_text'], y, test_size=0.20)

# Fit the pipeline
pipeline.fit(X_train, y_train)

# accuracy
accuracy = accuracy_score(y_test, pipeline.predict(X_test))
logging.info(f"Exact Match Ratio (Accuracy): {accuracy}")

# Micro-average F1 score
f1_micro = f1_score(y_test, pipeline.predict(X_test), average='micro')
logging.info(f"F1 Micro-Average: {f1_micro}")

logging.info("Saving the model to GCS...")
model_uri = save_model_to_gcs(pipeline, bucket_name, model_output_path)
print(f"Model saved to: {model_uri}")