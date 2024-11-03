# from claude (paid)

from google.cloud import storage, iam_v1
from google.cloud import aiplatform
from google.api_core import exceptions
import json

def verify_and_setup_permissions(
    project_id: str,
    bucket_name: str,
    service_account_email: str,
    credentials_path: str
):
    """
    Verify and setup necessary permissions for Vertex AI batch prediction
    
    Args:
        project_id: GCP project ID
        bucket_name: GCS bucket name
        service_account_email: Service account email to check/setup
        credentials_path: Path to credentials JSON file
    """
    required_roles = [
        "roles/storage.objectViewer",
        "roles/storage.buckets.get",
        "roles/aiplatform.user"
    ]
    
    # Initialize clients
    storage_client = storage.Client.from_service_account_json(credentials_path)
    iam_client = iam_v1.IAMClient.from_service_account_json(credentials_path)
    
    # 1. Verify bucket exists and permissions
    try:
        bucket = storage_client.get_bucket(bucket_name)
        print(f"✓ Bucket {bucket_name} exists")
    except exceptions.NotFound:
        print(f"✗ Bucket {bucket_name} not found!")
        return
    
    # 2. Get current IAM policy
    policy = bucket.get_iam_policy()
    
    # 3. Check and add necessary permissions
    for role in required_roles:
        role_exists = False
        for binding in policy.bindings:
            if binding["role"] == role:
                if f"serviceAccount:{service_account_email}" in binding["members"]:
                    print(f"✓ {role} already exists for {service_account_email}")
                    role_exists = True
                    break
        
        if not role_exists:
            print(f"Adding {role} for {service_account_email}")
            policy.bindings.append(
                {"role": role, "members": [f"serviceAccount:{service_account_email}"]}
            )
    
    # 4. Update bucket IAM policy
    bucket.set_iam_policy(policy)
    
    # 5. Verify Vertex AI service agent permissions
    vertex_sa = f"service-{project_id}@gcp-sa-aiplatform.iam.gserviceaccount.com"
    vertex_roles = [
        "roles/storage.objectViewer",
        "roles/aiplatform.serviceAgent"
    ]
    
    policy = bucket.get_iam_policy()
    for role in vertex_roles:
        role_exists = False
        for binding in policy.bindings:
            if binding["role"] == role:
                if f"serviceAccount:{vertex_sa}" in binding["members"]:
                    print(f"✓ {role} exists for Vertex AI service agent")
                    role_exists = True
                    break
        
        if not role_exists:
            print(f"Adding {role} for Vertex AI service agent")
            policy.bindings.append(
                {"role": role, "members": [f"serviceAccount:{vertex_sa}"]}
            )
            bucket.set_iam_policy(policy)

# Usage example
setup_params = {
    "project_id": "btibert-ba882-fall24",
    "bucket_name": "btibert-ba882-fall24-vertex-models",
    "service_account_email": "vertex-ai-sa@btibert-ba882-fall24.iam.gserviceaccount.com",
    "credentials_path": "/home/btibert/gcp/btibert-ba882-fall24-cdb40ea7a8ee.json"
}

verify_and_setup_permissions(**setup_params)