######
## simple script for now to deploy functions
## deploys all, which may not be necessary for unchanged resources
######

# setup the project
gcloud config set project btibert-ba882-fall24

# schema setup
gcloud functions deploy dev-schema-setup \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/schema-setup \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 256MB 