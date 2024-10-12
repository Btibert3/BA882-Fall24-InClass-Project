# The Machine Learning Datasets job

# imports
import requests
import json
from prefect import flow, task

# helper function - generic invoker
def invoke_gcf(url:str, payload:dict):
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

@task(retries=2)
def post_length():
    """Setup the stage schema"""
    url = "https://us-central1-btibert-ba882-fall24.cloudfunctions.net/ml-post-length"
    resp = invoke_gcf(url, payload={})
    return resp

@task(retries=2)
def post_tags():
    """Extract the RSS feeds into JSON on GCS"""
    url = "https://us-central1-btibert-ba882-fall24.cloudfunctions.net/ml-post-tags"
    resp = invoke_gcf(url, payload={})
    return resp


# the job
@flow(name="blogs-ml-datasets", log_prints=True)
def ml_datasets():
    # these are independent tasks
    post_length()
    post_tags()

# the job
if __name__ == "__main__":
    ml_datasets()