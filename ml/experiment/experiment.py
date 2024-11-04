from google.cloud import aiplatform

# tut: https://cloud.google.com/vertex-ai/docs/experiments/log-data
# docs: https://cloud.google.com/vertex-ai/docs/experiments/create-experiment

project_id = 'btibert-ba882-fall24'
gcp_region = 'us-central1'
exp_name = "my-fancy-experiment"


aiplatform.init(project=project_id, 
                location=gcp_region,
                experiment=exp_name,
                experiment_description="My meaningful description here",
                experiment_tensorboard=None)

# no spaces, regex [a-z0-9][a-z0-9-]{0,127}
aiplatform.start_run(run="post-length-1")

metrics = {
    "r2": 0.92,           # Replace with your R² value
    "mape": 8.5,          # Replace with your MAPE value (percentage)
    "mae": 3.2            # Replace with your MAE value
}

params = {
    'max_tokens': 5000,
    'ngram': str((1,2)),
    'model': 'LinearRegression'
}

aiplatform.log_metrics(metrics)
aiplatform.log_params(params)
aiplatform.end_run()

experiments_df = aiplatform.get_experiment_df()

## the experiment is the search space fo the task objective
## runs are the various slices of the test (model, output, params)
## 