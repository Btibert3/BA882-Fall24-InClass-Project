# imports
import functions_framework
import joblib
import json
from gcsfs import GCSFileSystem

# the hardcoded model on GCS
GCS_BUCKET = "btibert-ba882-fall24-vertex-models"
GCS_PATH = "models/post-length/"
FNAME = "model.joblib"
GCS = f"gs://{GCS_BUCKET}/{GCS_PATH}{FNAME}"

# load the model
with GCSFileSystem().open(GCS, 'rb') as f:
    model_pipeline = joblib.load(f)
print("loaded the model from GCS")

@functions_framework.http
def task(request):
    "Make predictions for the model"

    # Parse the request data
    request_json = request.get_json(silent=True)

    # load the data key which is a list of text for inference
    data_list = request_json.get('data')
    print(f"data: {data_list}")

    preds = model_pipeline.predict(data_list)

    # convert to a list for return
    preds_list = preds.tolist()

    return {'predictions':preds_list}, 200