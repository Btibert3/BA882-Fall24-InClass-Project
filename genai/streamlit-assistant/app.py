import streamlit as st


pg = st.navigation([
    st.Page("assistants.py", title="Simple Chat Assistant", icon=":material/chat:"), 
    st.Page("chunking.py", title="LlamaIndex Intuition", icon=":material/text_snippet:"),
    st.Page("doc-compare.py", title="Document Comparison", icon=":material/assignment:")
    ])
pg.run()

