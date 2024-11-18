# imports
import functions_framework
from google.cloud import secretmanager
import duckdb
import pandas as pd
from pinecone import Pinecone, ServerlessSpec

# setup
project_id = 'btibert-ba882-fall24'
project_region = 'us-central1'
wh_secret_id = 'mother_duck'   
vecdb_secret_id = 'pinecone'
version_id = 'latest'


# db setup
db = 'awsblogs'
schema = "stage"
db_schema = f"{db}.{schema}"