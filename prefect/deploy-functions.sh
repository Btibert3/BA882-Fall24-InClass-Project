######
## simple script for now to deploy functions
## deploys all, which may not be necessary for unchanged resources
######

# setup the project
gcloud config set project btibert-ba882-fall24

# schema setup
echo "======================================================"
echo "deploying the schema setup"
echo "======================================================"

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

# extract rss
echo "======================================================"
echo "deploying the rss extractor"
echo "======================================================"

gcloud functions deploy dev-extract-rss \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/extract-rss \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 256MB 


# parse rss
echo "======================================================"
echo "deploying the rss parser"
echo "======================================================"

gcloud functions deploy dev-parse-rss \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/parse-rss \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512MB 


# load the feeds into raw and changes into stage
echo "======================================================"
echo "deploying the loader"
echo "======================================================"

gcloud functions deploy dev-load-rss \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/load-rss \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512MB  \
    --timeout 60s 


# load the feeds into raw and changes into stage
echo "======================================================"
echo "deploying the ml dataset: post-tags"
echo "======================================================"

gcloud functions deploy ml-post-tags \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/post-tags \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512MB  \
    --timeout 300s 


# load the feeds into raw and changes into stage
echo "======================================================"
echo "deploying the ml dataset: post-length"
echo "======================================================"

gcloud functions deploy ml-post-length \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/post-wc \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512MB  \
    --timeout 300s 