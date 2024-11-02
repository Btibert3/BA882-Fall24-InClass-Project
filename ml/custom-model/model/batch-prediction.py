from google.cloud import aiplatform

# Initialize the Vertex AI client
aiplatform.init(project="btibert-ba882-fall24", location="us-central1")

# Define model and batch prediction settings
model_id = "3491069264956227584"
input_gcs_uri = "gs://btibert-ba882-fall24-vertex-models/batch-predict/post-length/post_length_batch.csv"
output_gcs_uri = "gs://btibert-ba882-fall24-vertex-models/batch-predict/post-length/"
service_account = "your_service_account_email"

batch_predict_parameters = {
    "instances_format": "csv",  # Format of input data: 'csv' or 'jsonl'
    "gcs_source": input_gcs_uri,
    "gcs_destination_prefix": output_gcs_uri,
    "predictions_format": "jsonl"  # Format for output data
}

# Create a batch prediction job
batch_prediction_job = aiplatform.BatchPredictionJob.create(
    job_display_name="batch-prediction-post-length",
    model_name=model_id,
    gcs_source=batch_predict_parameters["gcs_source"],
    instances_format=batch_predict_parameters["instances_format"],
    gcs_destination_prefix=batch_predict_parameters["gcs_destination_prefix"],
    predictions_format=batch_predict_parameters["predictions_format"],
    machine_type="n1-standard-2",
    sync=True,  # Set to True to wait for the job to complete
    service_account=service_account
)

print(f"Batch prediction job submitted. Job ID: {batch_prediction_job.name}")