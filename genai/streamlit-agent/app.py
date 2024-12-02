# imports
import streamlit as st 
import os
import io

from google.cloud import secretmanager
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from pinecone import Pinecone, ServerlessSpec


GCP_PROJECT = 'btibert-ba882-fall24'
project_id = 'btibert-ba882-fall24'
GCP_REGION = "us-central1"

version_id = 'latest'
vector_secret = "pinecone"
vector_index = 'post-content'
EMBEDDING_MODEL = "text-embedding-005"

# secret manager pinecone
sm = secretmanager.SecretManagerServiceClient()
vector_name = f"projects/{project_id}/secrets/{vector_secret}/versions/{version_id}"
response = sm.access_secret_version(request={"name": vector_name})
pinecone_token = response.payload.data.decode("UTF-8")
pc = Pinecone(api_key=pinecone_token)
index = pc.Index(vector_index)
print(f"index stats: {index.describe_index_stats()}")

# vertex ai
vertexai.init(project=project_id, location=GCP_REGION)
llm = GenerativeModel("gemini-1.5-pro-001", )
embedder = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
TASK = "RETRIEVAL_QUERY"


############################################## streamlit setup


st.image("https://questromworld.bu.edu/ftmba/wp-content/uploads/sites/42/2021/11/Questrom-1-1.png")
st.title("Blog Search")


################### sidebar <---- I know, we can do other layouts, easy for POCs

st.sidebar.title("Search the blogs")

search_query = st.sidebar.text_area("What are you looking to learn?")

top_k = st.sidebar.slider("Top K", 1, 15, step=1)

search_button = st.sidebar.button("Run the things!")


################### main

# Main action: Handle search
if search_button:
    if search_query.strip():
        # Get embedding
        embedding_input = TextEmbeddingInput(text=search_query, task_type=TASK)
        embedding_result = embedder.get_embeddings([embedding_input])
        embedding = embedding_result[0].values  # Assuming one input, get the embedding vector

        # search pincone
        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )

        # Display the results
        st.write(results)
    else:
        st.warning("Please enter a search query!")


