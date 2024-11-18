# inspect motherduck for new records not part of this job, 
# for delta, grab the ids to be parsed downstream

import functions_framework
from google.cloud import secretmanager
import duckdb
import datetime
import uuid

# settings
project_id = 'btibert-ba882-fall24'
secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
version_id = 'latest'

# db setup
db = 'awsblogs'
schema = "genai"
db_schema = f"{db}.{schema}"

@functions_framework.http
def task(request):

    # job_id
    job_id = datetime.datetime.now().strftime("%Y%m%d%H%M") + "-" + str(uuid.uuid4())


    # instantiate the services 
    sm = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = sm.access_secret_version(request={"name": name})
    md_token = response.payload.data.decode("UTF-8")

    # initiate the MotherDuck connection through an access token through
    md = duckdb.connect(f'md:?motherduck_token={md_token}') 

    ##################################################### get the records delta

    sql = """
    select 
        p.id 
    from 
        awsblogs.stage.posts p
    where 
        p.id not in (select id from awsblogs.genai.pinecone_posts)
    ;
    """
    
    df = md.sql(sql).df()
    print(df.shape)

    ids = df.id.to_list()

    return {
        "num_entries": len(ids), 
        "job_id": job_id, 
        "post_ids": ids
    }, 200



