# imports
import streamlit as st 
import PyPDF2
import os
import io
import vertexai
from vertexai.generative_models import GenerativeModel, Part

# https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference#supported-models
model = GenerativeModel("gemini-1.5-pro-001")

# resources:
# https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/document-understanding

############################################## project setup
GCP_PROJECT = 'btibert-ba882-fall24'
GCP_REGION = "us-central1"

vertexai.init(project=GCP_PROJECT, location=GCP_REGION)

# https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference#supported-models
model = GenerativeModel("gemini-1.5-pro-001", )

############################################## streamlit setup

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return None

# Function to compare texts using Vertex AI
def compare_texts(text1, text2):
    try:
        prompt = f"""
        Compare and contrast the following two texts:
        
        Text 1:
        {text1[:2000]}  # Limiting text length to avoid token limits
        
        Text 2:
        {text2[:2000]}
        
        Please provide:
        1. Main similarities between the documents
        2. Key differences
        3. Unique points in each document
        4. Overall summary of comparison
        
        Format the response in a clear, structured way.  Y
        """
        response = model.generate_content(prompt)

        return response.text
    except Exception as e:
        st.error(f"Error in Vertex AI comparison: {str(e)}")
        return None

st.title("PDF Comparison Analysis")



# File uploaders
file1 = st.sidebar.file_uploader("Upload first PDF", type=['pdf'], accept_multiple_files=False)
file2 = st.sidebar.file_uploader("Upload second PDF", type=['pdf'], accept_multiple_files=False)

if file1 and file2:
    st.success("PDFs processed successfully!  Click the Button below to start the analysis.")
    with st.spinner("Processing PDFs..."):
        # Extract text from PDFs
        text1 = extract_text_from_pdf(file1)
        text2 = extract_text_from_pdf(file2)
        
    if text1 and text2:
        if st.button("Compare Documents"):
            with st.spinner("Analyzing documents..."):
                comparison_result = compare_texts(text1, text2)
                
                if comparison_result:
                    st.subheader("Comparison Results")
                    st.markdown(comparison_result)
                    
                    # Option to download comparison
                    st.download_button(
                        label="Download Comparison Results",
                        data=comparison_result,
                        file_name="comparison_results.txt",
                        mime="text/plain"
                    )
    else:
        st.error("Error processing one or both PDFs. Please try again.")








