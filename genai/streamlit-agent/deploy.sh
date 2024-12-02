
# setup the project
gcloud config set project btibert-ba882-fall24

echo "======================================================"
echo "build (no cache)"
echo "======================================================"

docker build --no-cache -t gcr.io/btibert-ba882-fall24/streamlit-rag-app .

echo "======================================================"
echo "push"
echo "======================================================"

docker push gcr.io/btibert-ba882-fall24/streamlit-rag-app

echo "======================================================"
echo "deploy run"
echo "======================================================"


gcloud run deploy streamlit-rag-app \
    --image gcr.io/btibert-ba882-fall24/streamlit-rag-app \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --memory 1Gi

