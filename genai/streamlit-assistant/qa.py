import streamlit as st 
import vertexai
from vertexai.generative_models import GenerativeModel, ChatSession
from unstructured.partition.auto import partition

st.title("PDF File Analysis")

st.sidebar.title("Upload a PDF")

f1 = st.sidebar.file_uploader("File 1", type=['pdf'], accept_multiple_files=False)





