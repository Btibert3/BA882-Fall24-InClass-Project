# source: https://chatgpt.com/share/67072a34-4ae8-8006-9262-9291548ef260

# imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from google.cloud import secretmanager
from google.cloud import storage
import os
import joblib
import duckdb
import pandas as pd

# the root GCS bucket - gcs fuse
BUCKET_ROOT = '/gcs/btibert-ba882-fall24-vertex-models/awsblogs-tags-classifier'

# Environment variables
PROJECT_ID = 'btibert-ba882-fall24'
SECRET_NAME = 'mother_duck'

# Initialize clients
storage_client = storage.Client()
secret_client = secretmanager.SecretManagerServiceClient()

def access_secret(secret_name):
    """Access secrets from Google Secret Manager."""
    name = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
    response = secret_client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")

def fetch_data():
    """Fetch data from Motherduck using the provided query."""
    secret = access_secret(SECRET_NAME)
    
    # use the md token grabbed above as secret to connect
    md = duckdb.connect(f'md:?motherduck_token={secret}') 
        
    sql = """
    with 
    posts as (
    select id, content_text
    from awsblogs.stage.posts
    ),

    top_tags as (
    select lower(term) as term, count(*) as total 
    from awsblogs.stage.tags 
    group by term
    order by total desc
    limit 20
    ),

    tags as (
    select t.post_id, lower(t.term) as term
    from awsblogs.stage.tags t
    inner join top_tags tt on lower(t.term) = lower(tt.term)
    )

    select
    p.id,
    p.content_text,
    string_agg(lower(t.term), ',') AS labels 
    from posts p
    inner join tags t on p.id = t.post_id 
    group by p.id, p.content_text
    """

    df = md.execute(sql).df()

    return df

def save_to_gcs(df, filename):
    """Save dataframe to Google Cloud Storage."""
    bucket = storage_client.bucket(BUCKET_ROOT)
    blob = bucket.blob(filename)
    blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")

def train_model(df):

    df['labels_clean'] = df['labels'].apply(lambda x: x.split(','))

    # Convert the labels into a multi-label binary format using MultiLabelBinarizer
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(df['labels_clean'])

    # Create a pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000)),  # Convert content_text into TF-IDF features
        ('clf', OneVsRestClassifier(LogisticRegression()))  # Train a multi-label classifier
    ])

    X_train, X_test, y_train, y_test = train_test_split(df['content_text'], y, test_size=0.15)

    # Fit the pipeline
    pipeline.fit(X_train, y_train)




    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model accuracy: {accuracy}")
    
    return model

def save_model(model, filename):
    """Save the trained model to Google Cloud Storage."""
    bucket = storage_client.bucket(GCS_BUCKET)
    blob = bucket.blob(filename)
    blob.upload_from_string(joblib.dumps(model), content_type="application/octet-stream")

def main():
    print("Fetching data from Motherduck...")
    df = fetch_data()

    print("Saving dataset to GCS...")
    save_to_gcs(df, "dataset.csv")

    print("Training model...")
    model = train_model(df)

    print("Saving model to GCS...")
    save_model(model, "trained_model.joblib")

if __name__ == "__main__":
    main()
