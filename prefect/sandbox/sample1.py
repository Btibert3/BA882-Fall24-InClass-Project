import requests
import json
from prefect import flow, task
from google.cloud import storage # not needed, we will use GCF and our other deploy to handle in the background

# Task to call Google Cloud Function
@task(retries=2)
def call_cloud_function(gcf_url: str, payload: dict):
    """Call a Google Cloud Function with a given payload"""
    response = requests.post(gcf_url, data=payload)
    response.raise_for_status()
    return response.json()

# Task to save artifacts to Google Cloud Storage
@task
def save_to_gcs(data: dict, bucket_name: str, destination_blob_name: str):
    """Save data to Google Cloud Storage"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(str(data))  # Convert the dictionary to a string
    return f"File saved to {bucket_name}/{destination_blob_name}"

# Prefect Flow
@flow(log_prints=True)
def gcf_prefect_flow(gcf_url: str, payload: dict, bucket_name: str, destination_blob_name: str):
    """Orchestrates calling a GCF and saving the result to GCS"""
    # Call the Google Cloud Function
    response = call_cloud_function(gcf_url, payload)
    print(f"Received response from GCF: {response}")

    # Save the response to GCS
    save_result = save_to_gcs(response, bucket_name, destination_blob_name)
    print(save_result)

# Example invocation
if __name__ == "__main__":
    gcf_url = "https://us-central1-btibert-ba882-fall24.cloudfunctions.net/wf-entry"
    payload = {"message": "Hello from Prefect"}
    bucket_name = "btibert882_24_sandbox"
    destination_blob_name = "artifact.json"

    gcf_prefect_flow(gcf_url=gcf_url, payload=payload, bucket_name=bucket_name, destination_blob_name=destination_blob_name)
