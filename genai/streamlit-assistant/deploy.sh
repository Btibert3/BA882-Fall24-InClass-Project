
# setup the project
gcloud config set project btibert-ba882-fall24

echo "======================================================"
echo "build (no cache)"
echo "======================================================"

docker build --no-cache -t gcr.io/btibert-ba882-fall24/streamlit-genai-apps .

echo "======================================================"
echo "push"
echo "======================================================"

docker push gcr.io/btibert-ba882-fall24/streamlit-genai-apps

echo "======================================================"
echo "deploy run"
echo "======================================================"


gcloud run deploy streamlit-genai-apps \
    --image gcr.io/btibert-ba882-fall24/streamlit-genai-apps \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --memory 1Gi

