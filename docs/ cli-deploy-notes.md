# About

Code samples to deploy.

#if necessary
gcloud functions delete schema-setup --region=us-central1

make sure signed into project and authorized (lower left, cloud icon with project)

#1

gcloud config set project btibert-ba882-fall24

#2
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable bigquery.googleapis.com




```
gcloud functions deploy md-extract \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point main \
    --source ./functions/md-extract \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512MB 
```