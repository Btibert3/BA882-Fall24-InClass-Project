from google.cloud import aiplatform

def deploy_model(
    project_id: str,
    region: str,
    model_id: str,
    machine_type: str = "n2-standard-2",
    min_replica_count: int = 1,
    max_replica_count: int = 1
):
    """
    Deploy a model to Vertex AI.
    
    Args:
        project_id: Your GCP project ID
        region: Region to deploy to (e.g., 'us-central1')
        model_id: The ID of your uploaded model
        machine_type: The machine type to use for deployment
        min_replica_count: Minimum number of replicas
        max_replica_count: Maximum number of replicas
    
    Returns:
        The deployed endpoint
    """
    # Initialize Vertex AI
    aiplatform.init(
        project=project_id,
        location=region
    )
    
    # Get the model
    model = aiplatform.Model(model_id)
    
    # Deploy the model
    endpoint = model.deploy(
        machine_type=machine_type,
        min_replica_count=min_replica_count,
        max_replica_count=max_replica_count,
        sync=True  # Wait for deployment to complete
    )
    
    print(f"Model deployed to endpoint: {endpoint.resource_name}")
    return endpoint

# Example usage
if __name__ == "__main__":
    # Your project details
    PROJECT_ID = "btibert-ba882-fall24"
    REGION = "us-central1"
    MODEL_ID = "7539805329962303488"  # You'll need to get this from the uploaded model - its called name in the API, or id on the console
    
    # Deploy the model
    endpoint = deploy_model(
        project_id=PROJECT_ID,
        region=REGION,
        model_id=MODEL_ID,
    )