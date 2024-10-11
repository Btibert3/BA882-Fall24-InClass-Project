# imports
from google.cloud import storage
from google.cloud import aiplatform
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

logging.basicConfig(level=logging.INFO)

# settings
project_id = 'btibert-ba882-fall24'
gcp_region = 'us-central1'
bucket = 'btibert-ba882-fall24-vertex-models'
training_data_path = 'training-data/post-tags/data.parquet'
model_output_path = 'models/post-tags/'

# Read training data from GCS
def load_data_from_gcs(bucket_name, file_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    blob.download_to_filename('/tmp/data.parquet')
    return pd.read_parquet('/tmp/data.parquet')

# Save model to GCS
def save_model_to_gcs(model, bucket_name, model_output_path):
    client = storage.Client()
    bucket = client.bucket(bucket_name)  # Convert the bucket name string to a Bucket object
    model_filename = 'tags_model.joblib'
    model_path = os.path.join('/tmp', model_filename)
    joblib.dump(model, model_path)
    blob = bucket.blob(os.path.join(model_output_path, model_filename))  # Correctly access blob
    blob.upload_from_filename(model_path)
    return os.path.join('gs://', bucket_name, model_output_path)


# Register model with Vertex AI
def register_model_in_vertex_ai(model_uri, display_name):
    aiplatform.init(project=project_id, location=gcp_region)
    
    model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=model_uri,
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest"
    )
    return model

# Train model
def train_model():
    logging.info("Loading data from GCS...")
    df = load_data_from_gcs(bucket, training_data_path)

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
    X_train, X_test, y_train, y_test = train_test_split(df['content_text'], y, test_size=0.15)

    # Fit the pipeline
    pipeline.fit(X_train, y_train)

    # Save the model to GCS
    logging.info("Saving the model to GCS...")
    model_uri = save_model_to_gcs(pipeline, bucket, model_output_path)

    logging.info(f"Model saved to {model_uri}")

    # Register the model in Vertex AI
    logging.info("Registering the model with Vertex AI...")
    registered_model = register_model_in_vertex_ai(model_uri, display_name="post-tags-model")

    logging.info("Training and registration completed successfully.")

if __name__ == '__main__':
    train_model()
