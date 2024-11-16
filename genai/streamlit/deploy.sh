
# setup the project
gcloud config set project btibert-ba882-fall24

echo "======================================================"
echo "build (no cache)"
echo "======================================================"

docker build --no-cache -t gcr.io/btibert-ba882-fall24/streamlit-poc .

echo "======================================================"
echo "push"
echo "======================================================"

docker push gcr.io/btibert-ba882-fall24/streamlit-poc

echo "======================================================"
echo "deploy run"
echo "======================================================"


gcloud run deploy streamlit-poc \
    --image gcr.io/btibert-ba882-fall24/streamlit-poc \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --memory 1Gi

