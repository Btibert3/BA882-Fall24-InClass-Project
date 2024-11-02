# Variables
PROJECT_ID=btibert-ba882-fall24
REGION=us-central1
TRAIN_IMAGE_NAME=post-length-train
TRAIN_IMAGE_URI=gcr.io/$PROJECT_ID/$TRAIN_IMAGE_NAME:latest


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
echo "build the training image locally and then push"
echo "======================================================"

docker build -t $TRAIN_IMAGE_URI .
docker push $TRAIN_IMAGE_URI


echo "======================================================"
echo "kickoff a custom training job"
echo "======================================================"

gcloud ai custom-jobs create \
  --region=$REGION \
  --display-name=post-length-scikit-training \
  --config=worker-pool-spec.yaml