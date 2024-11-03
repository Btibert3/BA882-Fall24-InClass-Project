from google.cloud import aiplatform
from google.cloud.aiplatform import pipeline_jobs
from google.cloud.aiplatform_v1.types import ModelEvaluation
from google.auth import load_credentials_from_file
import json

CUSTOM_SA = "vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com"
PROJECT_ID = "btibert-ba882-fall24"
LOCATION = "us-central1"
BUCKET_NAME = "btibert-ba882-fall24-vertex-models"

credentials, _ = load_credentials_from_file(
    "/home/btibert/gcp/btibert-ba882-fall24-cdb40ea7a8ee.json",
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

# Initialize Vertex AI
aiplatform.init(
    credentials=credentials,
    project=PROJECT_ID,
    location=LOCATION,
    service_account=CUSTOM_SA
)

# First create the batch prediction job component
def create_batch_prediction_job(
    model_name,
    gcs_source_uri,
    gcs_dest_uri,
    service_account
):
    batch_prediction_job = aiplatform.BatchPredictionJob.create(
        job_display_name="regression-eval-batch-predict",
        model_name=model_name,
        gcs_source=gcs_source_uri,
        gcs_destination_prefix=gcs_dest_uri,
        service_account=service_account,
        machine_type="n1-standard-4",
        sync=True  # Wait for completion
    )
    return batch_prediction_job

# Create evaluation component
def create_model_evaluation(
    model_name,
    predictions_path,
    target_field,
    service_account
):
    model = aiplatform.Model(model_name=model_name)
    
    eval_job = model.create_evaluation_job(
        evaluation_job_display_name="custom-regression-eval",
        predictions_format="jsonl",
        predictions_gcs_source=predictions_path,
        target_field_name=target_field,
        service_account=service_account
    )
    return eval_job

# Main execution function
def run_custom_evaluation_pipeline():
    # Setup paths
    model_name = "projects/btibert-ba882-fall24/locations/us-central1/models/3491069264956227584@1"
    source_uri = f"gs://{BUCKET_NAME}/batch-predict/post-length/post_length_batch_sample.csv"
    predictions_uri = f"gs://{BUCKET_NAME}/evaluations/predictions"
    
    try:
        # Step 1: Run batch prediction
        print("Starting batch prediction...")
        batch_job = create_batch_prediction_job(
            model_name=model_name,
            gcs_source_uri=source_uri,
            gcs_dest_uri=predictions_uri,
            service_account=CUSTOM_SA
        )
        
        # Get the predictions path from batch job output
        predictions_path = batch_job.output_info.gcs_output_directory
        print(f"Batch prediction completed. Output at: {predictions_path}")
        
        # Step 2: Create and run evaluation
        print("Starting model evaluation...")
        eval_job = create_model_evaluation(
            model_name=model_name,
            predictions_path=predictions_path,
            target_field="word_count",
            service_account=CUSTOM_SA
        )
        
        # Wait for evaluation to complete
        eval_job.wait()
        
        # Get evaluation results
        eval_metrics = eval_job.get_model_evaluation()
        print("Evaluation completed. Metrics:", eval_metrics)
        
        return {
            "batch_job_id": batch_job.resource_name,
            "eval_job_id": eval_job.resource_name,
            "evaluation_metrics": eval_metrics
        }
        
    except Exception as e:
        print(f"Error in evaluation pipeline: {str(e)}")
        raise


results = run_custom_evaluation_pipeline()





# from claude

from google.cloud import aiplatform

CUSTOM_SA = "vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com"

# Initialize Vertex AI
aiplatform.init(
    project='btibert-ba882-fall24',
    location='us-central1',
    service_account=CUSTOM_SA
)

# Create batch prediction job directly
batch_prediction_job = aiplatform.BatchPredictionJob.create(
    job_display_name="console-style-batch-predict",
    model_name="projects/btibert-ba882-fall24/locations/us-central1/models/3491069264956227584@1",
    instances_format='csv',  # Explicitly specify CSV format
    predictions_format='jsonl',  # Common output format
    gcs_source="gs://btibert-ba882-fall24-vertex-models/batch-predict/post-length/post_length_batch_sample.csv",
    gcs_destination_prefix="gs://btibert-ba882-fall24-vertex-models/batch-predict/predictions",
    machine_type="n1-standard-4",
    service_account=CUSTOM_SA,
    sync=True
)

print(f"Job resource name: {batch_prediction_job.resource_name}")
print(f"Job state: {batch_prediction_job.state}")
print(f"Job output location: {batch_prediction_job.output_info.gcs_output_directory if batch_prediction_job.output_info else 'No output yet'}")



# Now create the evaluation job using the batch prediction output
model = aiplatform.Model(
    model_name="projects/btibert-ba882-fall24/locations/us-central1/models/3491069264956227584@1"
)

evaluation = model.evaluate(
    prediction_type="regression",
    target_field_name="word_count",
    gcs_source_uris=["gs://btibert-ba882-fall24-vertex-models/batch-predict/post-length/post_length_batch_sample.csv"],  # Using original CSV file
    staging_bucket="gs://btibert-ba882-fall24-vertex-models/evaluations",
    evaluation_pipeline_display_name="regression-eval-simple",
    evaluation_metrics_display_name="regression-metrics",
    service_account=CUSTOM_SA,
    predictions_gcs_source=batch_prediction_job.output_info.gcs_output_directory  # Add predictions path
)

evaluation.wait()

print("\nEvaluation Results:")
print(f"Evaluation job: {evaluation}")



############# another attempt

from google.cloud import aiplatform

CUSTOM_SA = "vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com"

# Initialize Vertex AI
aiplatform.init(
    project='btibert-ba882-fall24',
    location='us-central1',
    service_account=CUSTOM_SA
)

# Define pipeline parameters
pipeline_job = aiplatform.PipelineJob(
    display_name="regression-evaluation-pipeline",
    template_path="evalutation_regression_pipeline.json",
    pipeline_root="gs://btibert-ba882-fall24-vertex-models/pipeline_root",
    parameter_values={
        "prediction_type": "regression",
        "target_field_name": "word_count",
        "model": "projects/btibert-ba882-fall24/locations/us-central1/models/3491069264956227584@1",
        "gcs_source_uri": "gs://btibert-ba882-fall24-vertex-models/batch-predict/post-length/post_length_batch_sample.csv",
        "batch_predict_instances_format": "csv",
        "batch_predict_predictions_format": "jsonl",
        "evaluation_display_name": "regression-eval",
    },
    enable_caching=False
)

# Run the pipeline
pipeline_job.submit(
    service_account=CUSTOM_SA,
    network=None  # Specify if you need a specific network
)

# Wait for completion
pipeline_job.wait()

print(f"Pipeline completed: {pipeline_job.state}")