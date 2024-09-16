#################################
# TASK: extract the latest from the RSS feeds and store
#################################

# imports
import requests
import feedparser   
import pandas as pd
import datetime
import uuid
from google.cloud import storage, bigquery
import json 
from io import BytesIO


############################################## setup

# storage client
storage_client = storage.Client()

# storage bucket 
bucket_name = "btibert882_24_sandbox"


# feeds
# NOTE: Maybe I am overlooking something, but it looks like the basic feed and itemized feeds are different
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


######################################################### the job task

def main(feeds=feeds, bucket_name=bucket_name):
    """
    Extract the latest from the RSS feeds and store in GCS
    """

    ######################################################### grab the feeds

    # for each feed in feeds, grab the rss feed and parse
    feed_list = []
    for feed in feeds:
        try:
            r = requests.get(feed)
            feed = feedparser.parse(r.content)
            print(feed.feed.title)
            feed_list.append(feed)
        except Exception as e:
            print(e)

    # TODO: above isn't great, refactor 
    # QUESTION: what could we do differently? why might we consider a refactor?


    ######################################################### flatten into a single object

    # flatten all the entries
    entries = []
    for feed in feed_list:
        entries.extend(feed.entries)

    # modular to help debugging later.  
    # WHY: Sometimes simple code can go a long way, especially when "speed" isn't a blocker for the project in its current form.
    # list of dictionaries as we are just being methodical step by step
    entry_data = []
    for entry in entries:
        entry_data.append(dict(entry))


    ######################################################### pandas inspection

    # the entries from the feeds
    entries = pd.DataFrame(entry_data)
    entries.shape

    # drop dupes here
    entries_drop = entries.drop_duplicates(subset=['link'])
    entries_drop.shape


    ######################################################### flatten into a single object

    # flatten back to a list of dictionaries 
    # TODO: This **should** be ok, but could introduce a very subtle bug in translation to a new form and back
    entries_deduped = entries_drop.to_dict('records')


    ######################################################### after light inspection, store

    # the job id (can be multiple times per day, but a timestamp like way to search)
    # NOTE:  this supports multiple jobs within the minute, but do we really need it that for our jobs? <--- Batch focused, but when does batch not suffice?
    JOB_ID = datetime.datetime.now().strftime("%Y%m%d%H%M") + "-" + str(uuid.uuid4())

    # write the deduped JSON to GCS
    blob_name = f"rss/{JOB_ID}/raw.json"

    # Save each JSON object on a new line in a file in memory
    json_buffer = BytesIO()
    for record in entries_deduped:
        json_buffer.write((json.dumps(record) + "\n").encode('utf-8'))
    json_buffer.seek(0)

    # Upload the JSON file to GCS
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_file(json_buffer, content_type="application/json")


    ######################################################### return the file to load

    # grab the path to the file as a string
    file_path = f"gs://{bucket_name}/{blob_name}"

    # TODO: are there some better practices around returning json over simple entries (a single string value)
    results = {
        'filepath': file_path,
        'jobid': JOB_ID,
        'bucket_id': bucket_name,
        'blob_name': blob_name
    }
    print(results)
    return results

    