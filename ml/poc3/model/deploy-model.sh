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

echo "======================================================"
echo "deploy the endpoint"
echo "======================================================"

# gcloud ai endpoints create \
#   --region=us-central1 \
#   --display-name=post-length-endpoint

# mangually adding in the values for the endpoint first, and then the model

gcloud ai endpoints deploy-model 2760514157043253248 \
  --region=us-central1 \
  --model=3491069264956227584 \
  --display-name=post-length-deployment \
  --machine-type=n1-standard-4 \
  --min-replica-count=1 \
  --max-replica-count=1 \
  --service-account=vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com \
  --traffic-split=0=100


# find the deployed model id
# gcloud ai endpoints describe 5499828630391357440 \
#     --region=us-central1

# undeploy the model - id grabbed from above
# gcloud ai endpoints undeploy-model 5499828630391357440 \
#     --region=us-central1 \
#     --deployed-model-id=4523928497856446464


# tear down the endpoint
# gcloud ai endpoints delete 5499828630391357440 \
#     --region=us-central1 --quiet