import streamlit as st
from llama_index.core.node_parser import TokenTextSplitter, SentenceSplitter

st.title("LlamaIndex")
st.markdown("https://docs.llamaindex.ai/en/stable/")

# Sidebar: Chunking Options
st.sidebar.header("Chunking Options")
chunk_strategy = st.sidebar.selectbox(
    "Choose a Chunking Strategy",
    ["Fixed Size", "Semantic (Sentences)", "Paragraph-based"]
)
chunk_size = st.sidebar.slider("Chunk Size (tokens/words)", 0, 1000, step=10, value=300)
chunk_overlap = st.sidebar.slider("Chunk Overlap", 0, 100, step=2, value=50)

# Text Input
st.header("Input Text")
input_text = st.text_area("Paste your text here:", height=200)

# Process Text
if st.button("Chunk Text"):
    st.subheader("Chunked Output")

    if not input_text.strip():
        st.error("Please provide some text to chunk.")
    else:
        # Initialize the parser based on the selected strategy
        if chunk_strategy == "Fixed Size":
            parser = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = parser.split_text(input_text)
        elif chunk_strategy == "Semantic (Sentences)":
            parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = parser.split_text(input_text)
        elif chunk_strategy == "Paragraph-based":
            # Paragraph-based chunking (splits by newlines)
            chunks = input_text.split("\n\n")  # Splitting by paragraphs

        # Display chunked output
        for idx, chunk in enumerate(chunks):
            st.write(f"**Chunk {idx+1}:**\n{chunk}\n")
