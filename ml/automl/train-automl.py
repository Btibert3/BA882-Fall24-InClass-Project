from google.cloud import aiplatform

aiplatform.init(
    project='btibert-ba882-fall24',
    location='us-central1',  
)

# Define your dataset parameters
dataset = aiplatform.TabularDataset.create(
    display_name="nhl-shots-2024",
    gcs_source="gs://btibert-ba882-fall24-vertex-models/training-data/automl/shots_2024.csv"  # Path to your data in GCS
)

# Create an AutoML training job
job = aiplatform.AutoMLTabularTrainingJob(
    display_name="automl-shots-traing",
    optimization_prediction_type="classification", 
    optimization_objective="minimize-log-loss"  
)

# Kick off the training
model = job.run(
    dataset=dataset,
    target_column="goal",  # Column that you want to predict
    training_fraction_split=0.8,
    validation_fraction_split=0.1,
    test_fraction_split=0.1,
    budget_milli_node_hours=1000,  # 1000 milli node hours = 1 node hour
    model_display_name="automl-shots-model"
)
