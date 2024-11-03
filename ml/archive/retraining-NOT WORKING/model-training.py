from google.cloud import aiplatform
from google.cloud.aiplatform.training_jobs import CustomTrainingJob

training_container_uri = "us-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest"
serving_container_uri = "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"


project_id = 'btibert-ba882-fall24'
gcp_region = 'us-central1'
staging_bucket = "gs://btibert-ba882-fall24-vertex-models/models/post-length-hybrid"


aiplatform.init(project=project_id,
                location=gcp_region,
                staging_bucket=staging_bucket)

job = aiplatform.CustomTrainingJob(
    display_name="post-length-pipeline",
    script_path="./trainer.py",
    container_uri=training_container_uri,
    model_serving_container_image_uri=serving_container_uri,
    model_description="Hybrid Approach",
)

model = job.run(
    model_display_name="post-length-pipeline",
    service_account='vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com',
    machine_type="e2-standard-4",
    replica_count=1,
    base_output_dir="gs://btibert-ba882-fall24-vertex-models/models/post-length-hybrid",
    sync=False  # True is default
)

# review the metrics from the logs

new_model = aiplatform.Model("projects/btibert-ba882-fall24/locations/us-central1/models/4911497550554464256@1")

# Define regression metrics from the logs
metrics = {
    "r2": 0.92,           # Replace with your R² value
    "mape": 8.5,          # Replace with your MAPE value (percentage)
    "mae": 3.2            # Replace with your MAE value
}


model_eval = new_model.create_evaluation(
            annotations=metrics,
            evaluation_type="custom_regression_metrics",
            evaluation_name=f"my-first-metrics"
        )






job = new_model.evaluate(
    prediction_type="regression",
    target_field_name="MEDV",
    gcs_source_uris=[BUCKET_URI + "/" + "test_file_with_ground_truth.jsonl"],
    generate_feature_attributions=True,
)



----------

# Load model version
new_model = aiplatform.Model("projects/btibert-ba882-fall24/locations/us-central1/models/4911497550554464256@1")


# we didnt specify an experiment during init, lets do that now
aiplatform.init(project=project_id,
                location=gcp_region,
                staging_bucket=staging_bucket,
                experiment="My First experiment")

# Start an experiment to log metrics
experiment = aiplatform.Experiment.create(
    display_name="my_first_experiment"
)

# Start an experiment run
run = experiment.run(
    display_name="regression_evaluation_run",
    description="Evaluation of regression model with R2, MAPE, MAE"
)




# Define regression metrics from the logs
metrics = {
    "r2": 0.92,           # Replace with your R² value
    "mape": 8.5,          # Replace with your MAPE value (percentage)
    "mae": 3.2            # Replace with your MAE value
}

# Register evaluation metrics
evaluation = new_model.create_evaluation(
    display_name="Regression Evaluation for version 1",
    metrics=metrics
)

