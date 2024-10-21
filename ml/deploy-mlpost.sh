# set the project
gcloud config set project btibert-ba882-fall24


echo "======================================================"
echo "deploying the post length training function"
echo "======================================================"

gcloud functions deploy ml-postwc-train \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/ml-post_wc-train \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1GB  \
    --timeout 60s 

echo "======================================================"
echo "deploying the post length inference function"
echo "======================================================"

gcloud functions deploy ml-postwc-serve \
    --gen2 \
    --runtime python311 \
    --trigger-http \
    --entry-point task \
    --source ./functions/ml-post_wc-serve \
    --stage-bucket btibert-ba882-fall24-functions \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 1GB  \
    --timeout 60s 
