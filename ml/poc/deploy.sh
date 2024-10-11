
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
echo "build the docker image locally"
echo "======================================================"

docker build -t gcr.io/btibert-ba882-fall24/post-tags-trainer:latest .


echo "======================================================"
echo "push the image"
echo "======================================================"

docker push gcr.io/btibert-ba882-fall24/post-tags-trainer:latest

echo "======================================================"
echo "kickoff a custom training job"
echo "======================================================"

gcloud ai custom-jobs create \
  --region=us-central1 \
  --display-name=post-tags-trainer-job \
  --config=worker-pool-spec.yaml

