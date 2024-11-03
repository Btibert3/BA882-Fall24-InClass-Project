import os
from google.cloud import aiplatform
from kfp import compiler
from kfp.dsl import component, pipeline, Input, Output, Artifact

from google_cloud_pipeline_components.v1.model import ModelGetOp
from google_cloud_pipeline_components.v1.batch_predict_job import ModelBatchPredictOp
from google_cloud_pipeline_components.v1.model_evaluation import ModelEvaluationRegressionOp

# Initialize Vertex AI
PROJECT_ID = 'btibert-ba882-fall24'
REGION = 'us-central1'
SERVICE_ACCOUNT = 'vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com'
BUCKET_NAME = 'gs://btibert-ba882-fall24-vertex-models'

aiplatform.init(
    project=PROJECT_ID,
    location=REGION,
    staging_bucket=BUCKET_NAME,
    service_account=SERVICE_ACCOUNT,
)

# Helper component to wrap a string into a list
@component
def create_list(item: str) -> list:
    return [item]

# Define the pipeline
@pipeline(name='custom-evaluation-pipeline')
def custom_evaluation_pipeline(
    project_id: str,
    region: str,
    model_id: str,  # Changed parameter name
    gcs_source_uri: str,
    target_field_name: str,
    machine_type: str = 'n1-standard-4',
):
    # Wrap gcs_source_uri into a list
    gcs_source_uris_task = create_list(item=gcs_source_uri)

    # Retrieve the model as an artifact
    model_get_task = ModelGetOp(
        project=project_id,
        location=region,
        model_name=model_id,  # Pass only the model ID
    )

    # Batch prediction step
    batch_prediction_job = ModelBatchPredictOp(
        project=project_id,
        location=region,
        model=model_get_task.outputs['model'],
        job_display_name='batch_prediction_job',
        gcs_source_uris=gcs_source_uris_task.output,
        instances_format='csv',
        predictions_format='jsonl',
        gcs_destination_output_uri_prefix=f'{BUCKET_NAME}/batch_predictions',
        machine_type=machine_type,
        starting_replica_count=1,
        max_replica_count=1,
        service_account=SERVICE_ACCOUNT,
    )

    # Wrap ground_truth_gcs_source into a list
    ground_truth_gcs_source_task = create_list(item=gcs_source_uri)

    # Evaluation step
    evaluation_job = ModelEvaluationRegressionOp(
        project=project_id,
        location=region,
        model=model_get_task.outputs['model'],
        target_field_name=target_field_name,
        predictions_gcs_source=batch_prediction_job.outputs['gcs_output_directory'],
        ground_truth_gcs_source=ground_truth_gcs_source_task.output,
    )

    # Export evaluation metrics to GCS
    @component(
        packages_to_install=['google-cloud-storage'],
        base_image='python:3.9',
    )
    def export_metrics_to_gcs(
        metrics: Input[Artifact],
        gcs_output_path: str,
    ):
        import json
        from google.cloud import storage

        client = storage.Client()
        bucket_name, *object_path = gcs_output_path.replace('gs://', '').split('/')
        object_name = '/'.join(object_path)

        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        with open(metrics.path) as f:
            data = json.load(f)

        blob.upload_from_string(json.dumps(data), content_type='application/json')

    export_metrics_to_gcs_task = export_metrics_to_gcs(
        metrics=evaluation_job.outputs['evaluation_metrics'],
        gcs_output_path=f'{BUCKET_NAME}/evaluation_metrics/metrics.json',
    )

# Compile the pipeline
pipeline_filename = 'custom_evaluation_pipeline.json'
compiler.Compiler().compile(
    pipeline_func=custom_evaluation_pipeline,
    package_path=pipeline_filename,
)

# Define pipeline parameters
model_id = '3491069264956227584'  # Use only the model ID
gcs_source_uri = 'gs://btibert-ba882-fall24-vertex-models/batch-predict/post-length/post_length_batch_sample.csv'
target_field_name = 'word_count'

# Run the pipeline
job = aiplatform.PipelineJob(
    display_name='custom-evaluation-pipeline',
    template_path=pipeline_filename,
    pipeline_root=f'{BUCKET_NAME}/pipeline_root',
    parameter_values={
        'project_id': PROJECT_ID,
        'region': REGION,
        'model_id': model_id,
        'gcs_source_uri': gcs_source_uri,
        'target_field_name': target_field_name,
    },
    enable_caching=False,
)

# Pass 'service_account' to the 'run' method
job.run(service_account=SERVICE_ACCOUNT)
