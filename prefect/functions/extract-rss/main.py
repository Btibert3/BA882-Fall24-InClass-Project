# imports

from google.cloud import secretmanager
from google.cloud import storage
import requests
import feedparser
import json
import datetime
import uuid

# settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'
bucket_name = 'btibert-ba882-fall24-awsblogs'


####################################################### helpers

def upload_to_gcs(bucket_name, job_id, data):
    """Uploads data to a Google Cloud Storage bucket."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob_name = f"jobs/{job_id}/extracted_entries.json"
    blob = bucket.blob(blob_name)

    # Upload the data (here it's a serialized string)
    blob.upload_from_string(data)
    print(f"File {blob_name} uploaded to {bucket_name}.")

    return {'bucket_name':bucket_name, 'blob_name': blob_name}


####################################################### core task

@functions_framework.http
def task(request):

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

    ####################################### get the feeds

    feeds = [
        'https://aws.amazon.com/blogs/big-data/feed/',
        'https://aws.amazon.com/blogs/compute/feed/',
        'https://aws.amazon.com/blogs/database/feed/',
        'https://aws.amazon.com/blogs/machine-learning/feed/',
        'https://aws.amazon.com/blogs/containers/feed/',
        'https://aws.amazon.com/blogs/infrastructure-and-automation/feed/',
        'https://aws.amazon.com/blogs/aws/feed/',
        'https://aws.amazon.com/blogs/business-intelligence/feed/',
        'https://aws.amazon.com/blogs/storage/feed/'
    ]

    feed_list = []
    for feed in feeds:
        try:
            r = requests.get(feed)
            feed = feedparser.parse(r.content)
            print(feed.feed.title)
            feed_list.append(feed)
        except Exception as e:
            print(e)
            raise

    print(f"The length of the feed list is {len(feed_list)}")


    # flatten
    entries = []
    for feed in feed_list:
        entries.extend(feed.entries)
    print(f"There are {len(entries)} post entries")

    # to a json string
    entries_json = json.dumps(entries)

    # write to gcs
    gcs_path = upload_to_gcs(bucket_name, job_id, entries_json)

    return {
        "num_entries": len(entries), 
        "job_id": job_id, 
        "bucket_name":gcs_path.get('bucket_name'),
        "blob_name": gcs_path.get('blob_name')
    }, 200