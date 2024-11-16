import streamlit as st
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
# import duckdb
# import pandas as pd
# from google.cloud import secretmanager
# import numpy as np

# from itertools import combinations
# import networkx as nx
# from collections import Counter
# import matplotlib.pyplot as plt


# setup
# project_id = 'btibert-ba882-fall24'
# secret_id = 'mother_duck'   #<---------- this is the name of the secret you created
# version_id = 'latest'

# db setup
# db = 'awsblogs'
# schema = "stage"
# db_schema = f"{db}.{schema}"

# # instantiate the services 
# sm = secretmanager.SecretManagerServiceClient()

# Build the resource name of the secret version
# name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

# Access the secret version
# response = sm.access_secret_version(request={"name": name})
# md_token = response.payload.data.decode("UTF-8")

# initiate the MotherDuck connection through an access token through
# md = duckdb.connect(f'md:?motherduck_token={md_token}') 

# setup the connection for a chat sessions
# # https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference#supported-models
GCP_PROJECT = 'btibert-ba882-fall24'
GCP_REGION = "us-central1"

vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
model = GenerativeModel("gemini-1.5-flash-002")
chat_session = model.start_chat()

def get_chat_response(chat: ChatSession, prompt: str) -> str:
    text_response = []
    responses = chat.send_message(prompt, stream=True)
    for chunk in responses:
        text_response.append(chunk.text)
    return "".join(text_response)


############################################ Streamlit App

st.set_page_config(page_title="My Fancy Streamlit App", layout="wide")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []


# Dashboard layout
st.title("Streamlit as a GenAI Interface")
st.subheader("Simple to get Started, great for Prototypes and POCs")

# Sidebar filters for demo, not functional
st.sidebar.header("Inputs")
st.sidebar.markdown("One option is to use sidebars for inputs")


############ The Conversational Interface

st.markdown("---")




for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# prompt = st.chat_input("How can I help you today?")
# if prompt:
#     st.write(f"User has sent the following prompt: {prompt}")

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # get a response from the chat session with GCP
    response = get_chat_response(chat_session, prompt)
    # playback the response
    with st.chat_message("assistant"):
        st.markdown(response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})



