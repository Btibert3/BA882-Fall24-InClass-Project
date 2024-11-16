import streamlit as st


pg = st.navigation([
    st.Page("assistants.py", title="Simple Chat Assistant", icon=":material/chat:"), 
    st.Page("chunking.py", title="LlamaIndex Intuition", icon=":material/text_snippet:"),
    st.Page("qa.py", title="Document QA", icon=":material/contact_support:")
    ])
pg.run()
