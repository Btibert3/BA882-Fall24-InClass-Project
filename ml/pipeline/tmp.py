# Prefect training pipeline - experiments done first
# cloud function to train and write artifact to gcs
# register training run in cloud warehouse
# compare the model, if not existant or better, replace artifacts
# inference batch/real time is cloud function because fast, quick to iterate