#################################
# TASK: process the json from the previous step
#################################

# imports
import functions_framework
import datetime
from google.cloud import storage, bigquery
import json 
from io import BytesIO
import functions_framework

# format string to convert published date to a timestamp
format_str = "%a, %d %b %Y %H:%M:%S %z"

################################################### the task

@functions_framework.http
def main(request):

    storage_client = storage.Client()
    
    # get the raw json from gcs from the previous step
    request_json = request.get_json()
    bucket_id = request_json.get('bucket_id')
    blob_name = request_json.get('blob_name')

    # Get the bucket, blob, and read json
    bucket = storage_client.bucket(bucket_id)
    blob = bucket.blob(blob_name)
    blob_content = blob.download_as_text()

    # parse the JSONL (json lines) file
    lines = blob_content.splitlines()
    feeds = [json.loads(line) for line in lines]

    # parse the feed elements we want
    parsed_feeds = []
    for feed in feeds:
        parsed_feeds.append({
            'id': feed.get('id'),
            'url': feed.get('link'),
            'title': feed.get('title'),
            'published_date': datetime.datetime.strptime(feed.get('published'), format_str).isoformat(),
            'content': feed.get('content')[0].get('value'),
            'summary': feed.get('summary'),
            'ingest_timestamp': datetime.datetime.now().isoformat(),
            'job_id': request_json.get('jobid'),
            'raw_feed': json.dumps(feed)
        })
    
    ############################################################### JSON lines
    # write the JSONL to the same GCS path
    # Save each JSON object on a new line in a file in memory
    json_buffer = BytesIO()
    for record in parsed_feeds:
        json_buffer.write((json.dumps(record) + "\n").encode('utf-8'))
    json_buffer.seek(0)

    # Upload the JSON file to GCS
    job_id = request_json.get('jobid')
    bucket = storage_client.bucket(bucket_id)
    blob_name = f"rss/{job_id}/parsed.jsonl"
    blob = bucket.blob(blob_name)
    blob.upload_from_file(json_buffer, content_type="application/json")
    print(f"JSONL file uploaded to gs://{bucket_id}/{blob_name}")

    ############################################################### create the ingestion table

    # create a tmp copy of raw_posts for the job ingestion
    
    
    create_dataset_sql = f"""
    CREATE TABLE {tmp_table} LIKE `{dataset_id}.{table_id}`
    """

    # Execute the SQL to create the dataset
    try:
        bq_client.query(create_dataset_sql).result()
        print(f"Table {tmp_table} was created successfully.")
    except Exception as e:
        print(f"Error creating dataset {dataset_id}: {e}", 500)

    ############################################################### load into ingestion table

    # load the JSONL file from GCS into the tmp table
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
    )
    
    gcs_uri = f"gs://{bucket_id}/{blob_name}"
    destination = f"{dataset_id}.tmp_post_{job_id}"  # without the ticks

    try:
        load_job = bq_client.load_table_from_uri(
            gcs_uri,
            destination,
            job_config=job_config
        )
        print(f"Loaded the data into {destination}")
    except Exception as e:
        print(f"Error loading the extracted data into {destination}: {e}", 500)


    ############################################################### write the new records into the raw table

    delta_sql = f"""
    INSERT INTO `{dataset_id}.{table_id}`
    SELECT tmp.* 
    FROM {tmp_table} AS tmp
    LEFT JOIN `{dataset_id}.{table_id}` AS raw
    ON tmp.id = raw.id
    WHERE raw.id IS NULL;
    """

    # Execute the SQL to import the new records found
    try:
        bq_client.query(delta_sql).result()
        print(f"The record deltas were successfully evaluated")
    except Exception as e:
        print(f"Error evaluating the records: {e}", 500)


    ############################################################### cleanup the tmp table
    ## BQ has a limit, we may not hit it, but I tend to clean up these tmp tables

    cleanup_sql = f"""
    DROP TABLE `{destination}`;
    """

    # Execute the SQL to import the new records found
    try:
        bq_client.query(cleanup_sql).result()
        print(f"The tmp table {destination} was dropped")
    except Exception as e:
        print(f"Error dropping the table: {e}", 500)
    

    return {'statusCode':200}


    