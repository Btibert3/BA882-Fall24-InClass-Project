from google.cloud import aiplatform

# help
# https://cloud.google.com/python/docs/reference/aiplatform/latest/google.cloud.aiplatform#google_cloud_aiplatform_init


project_id = 'btibert-ba882-fall24'
gcp_region = 'us-central1'
exp_name = "my-second-experiment"

# perhaps a good example
# https://colab.research.google.com/github/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/official/experiments/comparing_local_trained_models.ipynb#scrollTo=12ab31563365
# line 22 hereL https://colab.research.google.com/github/GoogleCloudPlatform/vertex-ai-samples/blob/main/notebooks/official/experiments/comparing_local_trained_models.ipynb#scrollTo=u-iTnzt3B6Z_


aiplatform.init(project=project_id, 
                location=gcp_region,
                experiment=exp_name,
                experiment_description="My meaningful description here",
                experiment_tensorboard=None)

# no spaces, regex [a-z0-9][a-z0-9-]{0,127}
aiplatform.start_run(run="name-of-therun-details")

metrics = {
    "r2": 0.92,           # Replace with your R² value
    "mape": 8.5,          # Replace with your MAPE value (percentage)
    "mae": 3.2            # Replace with your MAE value
}

aiplatform.log_metrics(metrics)
aiplatform.end_run()