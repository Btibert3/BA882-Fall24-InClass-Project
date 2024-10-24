echo "======================================================"
echo "itemize the project"
echo "======================================================"

gcloud config set project btibert-ba882-fall24

echo "======================================================"
echo "ensure the APIs are enabled"
echo "======================================================"

gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com


echo "======================================================"
echo "build and push the image"
echo "======================================================"

docker build -t gcr.io/btibert-ba882-fall24/blog-post-length-model .

docker push gcr.io/btibert-ba882-fall24/blog-post-length-model

echo "======================================================"
echo "register the model"
echo "======================================================"


gcloud ai models upload \
  --region=us-central1 \
  --display-name=sklearn-post-length \
  --container-image-uri=gcr.io/btibert-ba882-fall24/blog-post-length-model \
  --container-predict-route=/predict \
  --container-health-route=/health


# echo "======================================================"
# echo "deploy the endpoint and assign the model to the endpoint"
# echo "this is you want a model to be available for real time predictions"
# echo "======================================================"

# Create an endpoint
# gcloud ai endpoints create \
#   --region=$REGION \
#   --display-name=post-tags-scikit-endpoint

# Deploy the model to the endpoint
# gcloud ai endpoints deploy-model \
#   --region=$REGION \
#   --endpoint=ENDPOINT_ID  # Replace with the actual endpoint ID
#   --model=MODEL_ID  # Replace with the registered model ID
#   --machine-type=n1-standard-2 \
#   --min-replica-count=1 \
#   --max-replica-count=1 \
#   --traffic-split=0=100

