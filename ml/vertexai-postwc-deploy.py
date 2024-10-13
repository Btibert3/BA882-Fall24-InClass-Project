import os
from google.cloud import aiplatform

# settings - references paths from the previous model
project_id = 'btibert-ba882-fall24'
gcp_region = 'us-central1'

def get_or_create_endpoint(endpoint_display_name):
    """Get an existing endpoint or create a new one if it doesn't exist."""
    aiplatform.init(project=project_id, location=gcp_region)
    
    # Check if the endpoint already exists
    endpoints = aiplatform.Endpoint.list(filter=f"display_name={endpoint_display_name}")
    if endpoints:
        endpoint = endpoints[0]
        print(f"Using existing endpoint: {endpoint.display_name}")
    else:
        # Create a new endpoint
        print(f"Creating new endpoint: {endpoint_display_name}")
        endpoint = aiplatform.Endpoint.create(display_name=endpoint_display_name)
    
    return endpoint

def deploy_model_to_endpoint(model_display_name, endpoint_display_name):
    """Deploy a model from the Model Registry to an endpoint using n1-standard-2 machine type."""
    # Initialize Vertex AI platform
    aiplatform.init(project=project_id, location=gcp_region)

    # Get the model from the registry
    models = aiplatform.Model.list(filter=f"display_name={model_display_name}")
    if not models:
        raise ValueError(f"Model {model_display_name} not found.")
    
    model = models[0]
    print(f"Found model: {model.display_name}")

    # Get or create an endpoint
    endpoint = get_or_create_endpoint(endpoint_display_name)

    # Deploy the model to the endpoint
    print(f"Deploying model '{model_display_name}' to endpoint '{endpoint_display_name}' using n1-standard-2 machine type...")
    model.deploy(
        endpoint=endpoint,
        deployed_model_display_name=model_display_name,
        machine_type="n1-standard-2",  # Cheaper machine type that doesn't scale to zero
        max_replica_count=1,  # Adjust based on your load
        traffic_split={"0": 100},  # 100% traffic to this model
    )
    
    print(f"Model deployed to endpoint: {endpoint.resource_name}")

if __name__ == '__main__':
    model_display_name = "post-length"  # Change this to your model's display name
    endpoint_display_name = "post-length-endpoint"  # Set a name for the endpoint
    deploy_model_to_endpoint(model_display_name, endpoint_display_name)
