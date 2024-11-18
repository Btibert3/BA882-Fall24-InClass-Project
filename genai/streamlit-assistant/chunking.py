import streamlit as st
from llama_index.core.node_parser import TokenTextSplitter, SentenceSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core.node_parser import LangchainNodeParser
from llama_index.core import Document

st.image("https://questromworld.bu.edu/ftmba/wp-content/uploads/sites/42/2021/11/Questrom-1-1.png")


st.title("LlamaIndex")
st.markdown("https://docs.llamaindex.ai/en/stable/")

# Sidebar: Chunking Options
st.sidebar.header("Chunking Options")
chunk_strategy = st.sidebar.selectbox(
    "Choose a Chunking Strategy",
    ["Fixed Size", "Semantic (Sentences)", "Paragraph-based", "RecursiveCharacterTextSplitter"]
)
chunk_size = st.sidebar.slider("Chunk Size (tokens/words)", 0, 1000, step=10, value=300)
chunk_overlap = st.sidebar.slider("Chunk Overlap", 0, 100, step=2, value=50)

st.sidebar.markdown("---")

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
            st.sidebar.markdown("The TokenTextSplitter attempts to split to a consistent chunk size according to raw token counts.")
        elif chunk_strategy == "Semantic (Sentences)":
            parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = parser.split_text(input_text)
            st.sidebar.markdown("The SentenceSplitter attempts to split text while respecting the boundaries of sentences.")
        elif chunk_strategy == "Paragraph-based":
            # Paragraph-based chunking (splits by newlines)
            chunks = input_text.split("\n\n")  # Splitting by paragraphs
            st.sidebar.markdown("The settings above are ignored, looks for '`\n\n`' to define paragraphs.")
        elif chunk_strategy == "RecursiveCharacterTextSplitter":
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            parser = LangchainNodeParser(text_splitter)
            document = Document(
                text=input_text,  # LlamaIndex uses 'text' instead of 'page_content'
                id_="doc-1"      # LlamaIndex uses 'id_' instead of 'id'
            )
            chunks = parser.get_nodes_from_documents([document])
            st.sidebar.markdown("""Llama-index plays nicely with Langchain! This text splitter is the recommended one for generic text. It is parameterized by a list of characters. It tries to split on them in order until the chunks are small enough. The default list is ["\n\n", "\n", " ", ""]. This has the effect of trying to keep all paragraphs (and then sentences, and then words) together as long as possible, as those would generically seem to be the strongest semantically related pieces of text.""")

        # Display chunked output
        for idx, chunk in enumerate(chunks):
            st.write(f"**Chunk {idx+1}:**\n{chunk}\n")
