import os
from google.cloud import aiplatform

# settings - references paths from the previous model
project_id = 'btibert-ba882-fall24'
gcp_region = 'us-central1'
bucket_name = 'btibert-ba882-fall24-vertex-models'
model_output_path = 'models/post-length/'

def register_model_in_vertex_ai(model_uri, display_name):
    """Register a model in Vertex AI using the correct serving image."""
    aiplatform.init(project=project_id, location=gcp_region)
    
    # Upload and register the model using the correct serving image
    model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=model_uri,
        serving_container_image_uri="us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-0:latest"  # Correct serving image
    )
    return model

if __name__ == '__main__':
    model_uri = os.path.join('gs://', bucket_name, model_output_path)
    print(f"model uri: {model_uri}")
    print("Uploading the model")
    register_model_in_vertex_ai(model_uri, "post-length")
