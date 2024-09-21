#################################
# TASK: process the json from the previous step
#################################

# imports
import functions_framework
import datetime
from google.cloud import storage, bigquery
import json 
from io import BytesIO


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

    bq_client = bigquery.Client()

    # create a tmp copy of raw_posts for the job ingestion
    dataset_id = "aws_blogs"  #ideally passed in from the prev step or env variable
    table_id = "raw_post" #ideally passed in from the prev step or env variable
    tmp_table = f"{dataset_id}.tmp_post_{job_id}"
    create_dataset_sql = f"""
    CREATE TABLE `{tmp_table}` LIKE `{dataset_id}.{table_id}`
    """

    # Execute the SQL to create the dataset
    try:
        bq_client.query(create_dataset_sql).result()
        print(f"Table {tmp_table} was created successfully.")
    except Exception as e:
        print(f"Error creating dataset {dataset_id}: {e}", 500)
        raise

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
        raise


    ############################################################### write the new records into the raw table

    # delta_sql = f"""
    # INSERT INTO `{dataset_id}.{table_id}`
    # SELECT tmp.* 
    # FROM `{tmp_table}` AS tmp
    # LEFT JOIN `{dataset_id}.{table_id}` AS raw
    # ON tmp.id = raw.id
    # WHERE raw.id IS NULL;
    # """
    # delta_sql = """
    # INSERT INTO `aws_blogs.raw_post` (id, url, title, published_date, content, summary, ingest_timestamp, job_id, raw_feed)
    # SELECT tmp.id, tmp.url, tmp.title, tmp.published_date, tmp.content, tmp.summary, tmp.ingest_timestamp, tmp.job_id, tmp.raw_feed
    # FROM `aws_blogs.tmp_post_202409171448-0bbe3e29-b4da-486c-9e66-6e07d830b882` AS tmp
    # LEFT JOIN `aws_blogs.raw_post` AS raw
    # ON tmp.id = raw.id
    # WHERE raw.id IS NULL;
    # """
    # print(f"the query to move the changed records: {delta_sql}")

    # query = "SELECT 1 AS test"
    # try:
    #     query_job = bq_client.query(query)
    #     result = query_job.result()
    #     print("Test query executed successfully:", list(result))
    # except Exception as e:
    #     print(f"Error executing test query: {e}")
    #     raise

    #Execute the SQL to import the new records found
    # try:
    #     query_job = bq_client.query(delta_sql)
    #     query_job.result()
    #     print(f"The record deltas were successfully evaluated")
    # except Exception as e:
    #     print(f"Error evaluating the records: {e}", 500)
    #     raise

    # source_table_id = f"{tmp_table}"  
    # destination_table_id = f"{dataset_id}.{table_id}"

    # # Configure the job
    # job_config = bigquery.CopyJobConfig()
    # job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND 

    # # Perform the CopyJob
    # try:
    #     copy_job = bq_client.copy_table(
    #         sources=source_table_id,
    #         destination=destination_table_id,
    #         job_config=job_config
    #     )
    #     copy_job.result()  # Waits for the job to complete
        
    #     print(f"Copy job completed successfully. Data moved from {source_table_id} to {destination_table_id}.")
    #     print(f"Job details: {copy_job.job_id}")
    # except Exception as e:
    #     print(f"Error during the CopyJob: {e}")
    #     raise

    # source_table_id = f"{tmp_table}"  
    # destination_table_id = f"{dataset_id}.{table_id}"
    # source_data = pandas_gbq.read_gbq(f"SELECT * FROM `{source_table_id}`", progress_bar_type=None)
    # destination_ids = pandas_gbq.read_gbq(f"SELECT id FROM `{destination_table_id}`", progress_bar_type=None)

    # # look for the deltas
    # deltas = source_data[~source_data['id'].isin(destination_ids['id'])]

    # # write as json lines to GCS
    # json_buffer = BytesIO()
    # for record in deltas.to_dict(orient='records'):
    #     json_buffer.write((json.dumps(record) + "\n").encode('utf-8'))
    # json_buffer.seek(0)

    # blob_name = f"rss/{job_id}/deltas.jsonl"
    # blob = bucket.blob(blob_name)
    # blob.upload_from_file(json_buffer, content_type="application/json")
    # print(f"JSONL file uploaded to gs://{bucket_id}/{blob_name}")


    ############################################################### cleanup the tmp table
    ## BQ has a limit, we may not hit it, but I tend to clean up these tmp tables

    # cleanup_sql = f"""
    # DROP TABLE `{destination}`;
    # """

    # # Execute the SQL to import the new records found
    # try:
    #     bq_client.query(cleanup_sql).result()
    #     print(f"The tmp table {destination} was dropped")
    # except Exception as e:
    #     print(f"Error dropping the table: {e}", 500)
    #     raise
    
    
    return {'statusCode':200}


    