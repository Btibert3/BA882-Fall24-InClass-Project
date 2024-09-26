# setup the project
gcloud config set project btibert-ba882-fall24


echo "======================================================"
echo "build (no cache)"
echo "======================================================"

docker build --no-cache -t gcr.io/btibert-ba882-fall24/quarto-render-service .

echo "======================================================"
echo "push"
echo "======================================================"

docker push gcr.io/btibert-ba882-fall24/quarto-render-service

echo "======================================================"
echo "deploy run"
echo "======================================================"

gcloud run deploy quarto-render-service \
    --image gcr.io/btibert-ba882-fall24/quarto-render-service \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --service-account etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com \
    --memory 1Gi
