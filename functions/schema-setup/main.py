# TASK:  Create the schema to ensure it exists.  This could be broken out into smaller tasks, but simple for now
# NOTE: I set my Service Account as GOOGLE_APPLICATION_CREDENTIALS in .bash_rc to mimic local and deployed code (set in the background via SA we define)

from google.cloud import bigquery
import functions_framework

@functions_framework.http
def main(request):
    # Initialize BigQuery client
    bq_client = bigquery.Client()

    # Define dataset and table names
    dataset_id = 'aws_blogs'
    table_id = 'raw_post'
    project_id = bq_client.project


    ############################################################ SCHEMA

    # SQL to create dataset if it does not exist
    create_dataset_sql = f"""
    CREATE SCHEMA IF NOT EXISTS `{project_id}.{dataset_id}`
    """

    # Execute the SQL to create the dataset
    try:
        bq_client.query(create_dataset_sql).result()
        print(f"Dataset {dataset_id} exists or created successfully.")
    except Exception as e:
        print(f"Error creating dataset {dataset_id}: {e}", 500)


    ############################################################ TABLES

    # SQL to create table if it does not exist
    # response_body is json string, summary is from the feed, content is parsed out as EtLT
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.{table_id}` (
        id STRING,
        url STRING,
        title STRING,
        published_date TIMESTAMP,
        content STRING,
        summary STRING,
        ingest_timestamp TIMESTAMP,
        job_id STRING,
        raw_feed STRING
    )
    """

    # Execute the SQL to create the table
    try:
        bq_client.query(create_table_sql).result()
        print(f"Table {table_id} in dataset {dataset_id} exists or created successfully.")
    except Exception as e:
        print(f"Error creating table {table_id} in dataset {dataset_id}: {e}", 500)

    # output of the function, could be way more verbose or handy
    return {'statusCode':200}
