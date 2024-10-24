# predictor.py
import os
from google.cloud import storage
import joblib
import flask
from flask import Flask, jsonify, request
import numpy as np
import pandas as pd

app = Flask(__name__)

# Initialize global model variable
model = None

def download_model():
    """Downloads the model file from GCS."""
    bucket_name = "btibert-ba882-fall24-vertex-models"
    model_path = "models/post-length/model.joblib"
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(model_path)
    
    local_path = "/tmp/model.joblib"
    blob.download_to_filename(local_path)
    return local_path

def load_model():
    """Loads the model into memory."""
    global model
    local_model_path = download_model()
    model = joblib.load(local_model_path)

@app.route('/predict', methods=['POST'])
def predict():
    """Makes a prediction based on the input data."""
    # Load model if not already loaded
    global model
    if model is None:
        load_model()
    
    # Get json request
    request_json = request.get_json()
    
    # Extract instances from the request
    instances = request_json["instances"]
    
    # Convert instances to pandas Series since that's what the pipeline expects
    # The pipeline was trained on df['title'] which is a pandas Series
    titles = pd.Series(instances[0] if isinstance(instances[0], str) else instances[0][0])
    
    # Make prediction using the pipeline
    predictions = model.predict(titles).tolist()
    
    # Return prediction response
    return jsonify({"predictions": predictions})

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    # Load model at startup
    load_model()
    
    # Run flask app
    app.run(host='0.0.0.0', port=8080)