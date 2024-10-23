from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import joblib
import logging
import numpy as np
from google.cloud import storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Post Tags Prediction Service")

# Pydantic models for request/response validation
class PredictionInstance(BaseModel):
    content_text: str

class PredictionRequest(BaseModel):
    instances: List[PredictionInstance]

class TagPrediction(BaseModel):
    tag: str
    probability: float

class InstancePrediction(BaseModel):
    predictions: List[TagPrediction]

class PredictionResponse(BaseModel):
    predictions: List[InstancePrediction]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    labels: Optional[List[str]] = None

class ModelService:
    def __init__(self):
        self.model = None
        self.labels = None
        self.model_loaded = False
        
    def load_model(self, gcs_path: str) -> None:
        """Load model and labels from Google Cloud Storage"""
        try:
            if self.model is None:
                logger.info(f"Loading model from {gcs_path}")
                
                # Parse GCS path
                bucket_name = gcs_path.split('/')[2]
                blob_path = '/'.join(gcs_path.split('/')[3:])
                
                # Download from GCS
                storage_client = storage.Client()
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_path)
                
                local_path = "/tmp/model.joblib"
                blob.download_to_filename(local_path)
                
                # Load model
                pipeline = joblib.load(local_path)
                self.model = pipeline
                
                # Extract labels (ensure they are the actual label names, not indices)
                try:
                    if hasattr(pipeline.named_steps['clf'], 'classes_'):
                        self.labels = list(pipeline.named_steps['clf'].classes_)
                    else:
                        logger.warning("No 'classes_' attribute found, using numbered labels.")
                        num_labels = len(pipeline.predict_proba([" "])[0])
                        self.labels = [f"label_{i}" for i in range(num_labels)]
                except AttributeError as e:
                    logger.warning(f"Could not extract labels: {e}")
                    num_labels = len(pipeline.predict_proba([" "])[0])
                    self.labels = [f"label_{i}" for i in range(num_labels)]
                
                self.model_loaded = True
                logger.info(f"Model loaded successfully with {len(self.labels)} labels")
                logger.info(f"Labels: {self.labels}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")


    async def predict(self, texts: List[str]) -> List[List[TagPrediction]]:
        """Make predictions on the input texts"""
        try:
            if not self.model_loaded:
                raise HTTPException(status_code=500, detail="Model not loaded")
            
            # Make predictions
            predictions = self.model.predict_proba(texts)
            
            # Convert predictions to list of TagPrediction objects
            predictions_with_labels = []
            for pred_array in predictions:
                # Create list of TagPrediction objects maintaining original order
                instance_preds = [
                    TagPrediction(tag=str(label), probability=float(prob))  # Ensure tag is a string
                    for label, prob in zip(self.labels, pred_array)
                ]
                predictions_with_labels.append(instance_preds)
            
            return predictions_with_labels
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# Initialize model service
model_service = ModelService()

@app.on_event("startup")
async def startup_event():
    """Load model when application starts"""
    model_service.load_model("gs://btibert-ba882-fall24-vertex-models/models/post-tags/model.joblib")

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Make predictions on the input instances
    
    Example request body:
    {
        "instances": [
            {"content_text": "example text 1"},
            {"content_text": "example text 2"}
        ]
    }
    """
    # Extract texts from instances
    texts = [instance.content_text for instance in request.instances]
    
    # Get predictions
    predictions_with_labels = await model_service.predict(texts)
    
    # Format response
    response_predictions = [
        InstancePrediction(predictions=instance_preds)
        for instance_preds in predictions_with_labels
    ]
    
    return PredictionResponse(predictions=response_predictions)

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        model_loaded=model_service.model_loaded,
        labels=model_service.labels if model_service.model_loaded else None
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)