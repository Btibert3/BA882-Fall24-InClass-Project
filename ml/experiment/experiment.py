from google.cloud import aiplatform

# tut: https://cloud.google.com/vertex-ai/docs/experiments/log-data
# docs: https://cloud.google.com/vertex-ai/docs/experiments/create-experiment

project_id = 'btibert-ba882-fall24'
gcp_region = 'us-central1'
exp_name = "post-length-revision-pl045"


aiplatform.init(project=project_id, 
                location=gcp_region,
                experiment=exp_name,
                experiment_description="Revisit different models to improve fit",
                experiment_tensorboard=None)

# no spaces, regex [a-z0-9][a-z0-9-]{0,127}
aiplatform.start_run(run="post-length-2")

metrics = {
    "r2": 0.94,           # Replace with your R² value
    "mape": 8.1,          # Replace with your MAPE value (percentage)
    "mae": 3.0            # Replace with your MAE value
}

params = {
    'max_tokens': 7500,
    'ngram': str((1,3)),
    'model': 'LinearRegression'
}

aiplatform.log_metrics(metrics)
aiplatform.log_params(params)
aiplatform.end_run()

experiments_df = aiplatform.get_experiment_df()

## the experiment is the search space fo the task objective
## runs are the various slices of the test (model, output, params)
## 