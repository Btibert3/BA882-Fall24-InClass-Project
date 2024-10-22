from fastapi import FastAPI
import joblib
from google.cloud import storage
from typing import List

app = FastAPI()

# Health check endpoint
@app.get("/")
async def health_check():
    return {"status": "ok"}


@app.post("/predict")
def predict_proba(texts: List[str]):
    proba = model.predict_proba(texts)
    return {"predictions": proba.tolist()}
