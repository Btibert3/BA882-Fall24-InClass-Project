# imports
import requests
from prefect import flow, task
from prefect.futures import wait
from prefect.task_runners import ThreadPoolTaskRunner

# helper function - generic invoker
def invoke_gcf(url:str, payload:dict):
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

# setup the schema in the warehouse and vector store (index)
@task(retries=2)
def schema_setup():
    """Setup the stage schema"""
    url = "https://us-central1-btibert-ba882-fall24.cloudfunctions.net/genai-schema-setup"
    resp = invoke_gcf(url, payload={})
    return resp

# get the posts that haven't been processed
@task(retries=2)
def collect():
    """Collect the posts that haven't been processed"""
    url = "https://us-central1-btibert-ba882-fall24.cloudfunctions.net/genai-schema-collector"
    resp = invoke_gcf(url, payload={})
    return resp

# process a post passed to it from an upstream task
@task(retries=3)
def ingest(payload):
    """For a given post id, embed the chunks to support GenAI workflows/"""
    url = "https://us-central1-btibert-ba882-fall24.cloudfunctions.net/genai-schema-ingestor"
    print(f"processing id: {payload.get('post_id')}")
    resp = invoke_gcf(url, payload=payload)
    return resp


# job that uses the threadpool to process posts in blocks, as they don't have any dependency
@flow(task_runner=ThreadPoolTaskRunner(max_workers=5), log_prints=True)
def job():

    result = schema_setup()
    print("The schema setup completed")

    collect_result = collect()
    post_ids = collect_result.get("post_ids")
    print(f"Posts to process: {len(post_ids)}")

    processed_posts = []

    for post_id in post_ids[:10]:
        processed_posts.append(ingest.submit({"post_id": post_id}))

    wait(processed_posts)

# the job
if __name__ == "__main__":
    job()

