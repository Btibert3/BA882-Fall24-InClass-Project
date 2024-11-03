from google.cloud import aiplatform
from google.auth import load_credentials_from_file

# appears to be required
credentials, _ = load_credentials_from_file(
    "/home/btibert/gcp/btibert-ba882-fall24-cdb40ea7a8ee.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

SA = "vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com"

# different auth
aiplatform.init(
    credentials=credentials,   #### <--- even after iam via pypi, this still fails, bizarre its needed .Why?
    service_account=SA,
    project='btibert-ba882-fall24',
    location='us-central1'
)

# NOTE:  even if owner, need to set IAM of bucket object viewer and creator, wild!

# grab the model -- should consider using the version
my_model = aiplatform.Model(
    model_name="projects/btibert-ba882-fall24/locations/us-central1/models/3491069264956227584@1"
)



my_evaluation_job = my_model.evaluate(
    prediction_type="regression",
    target_field_name="word_count",
    gcs_source_uris=["gs://btibert-ba882-fall24-vertex-models/batch-predict/post-length/post_length_batch_sample.csv"],
    staging_bucket="gs://btibert-ba882-fall24-vertex-models/models/post-length",
    evaluation_pipeline_display_name="my-pipeline-name-changeme",
    evaluation_metrics_display_name="metrics-name-changeme",
    service_account=SA
)

# creates a pipeline above -> note the IAM even owner, needs additional things
# bucket level on vertex service agent


# this hooks into the sync job and will print
my_evaluation_job.wait()

# https://claude.ai/chat/ed26334e-8cc4-494f-a761-252c4f49f31b
# ^^this might be the disconnect, the idea of the service agent? email 
# ^^ this could be a reason to try a net new service account for all ML if the tests work.  I changed all sorts of bucket and IAM bits for vertex


## still failing, this is bonkers.  