#!/bin/bash

# Set variables
PROJECT_ID="btibert-ba882-fall24"
BUCKET_NAME="btibert-ba882-fall24-vertex-models"

# Grant permissions to the Vertex AI Service Account
echo "Granting Vertex AI service account permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:service-1077323016672@gcp-sa-aiplatform.iam.gserviceaccount.com" \
    --role="roles/storage.objectViewer"

# Grant permissions to allow Vertex AI to create and use temporary service accounts
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:service-1077323016672@gcp-sa-aiplatform.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Add bucket-level IAM bindings
echo "Granting bucket-level permissions..."
gsutil iam ch \
    allUsers:objectViewer \
    gs://${BUCKET_NAME}

# Add a bucket IAM policy that allows temporary service accounts
cat > /tmp/bucket_policy.json << EOL
{
  "bindings": [
    {
      "members": [
        "serviceAccount:service-1077323016672@gcp-sa-aiplatform.iam.gserviceaccount.com",
        "projectViewer:${PROJECT_ID}",
        "projectEditor:${PROJECT_ID}",
        "projectOwner:${PROJECT_ID}"
      ],
      "role": "roles/storage.admin"
    }
  ]
}
EOL

gsutil iam set /tmp/bucket_policy.json gs://${BUCKET_NAME}

echo "Setup complete. Please wait a few minutes for all IAM permissions to propagate."