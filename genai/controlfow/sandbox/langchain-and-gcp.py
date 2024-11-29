# pip install langchain-google-genai <- yet another version, geared towards gemini but with GOOGLE_APP_CREDENTIALS it seems to be painless
# https://python.langchain.com/api_reference/google_genai/index.html

# poke around to see how the service account/creds can be intergrated easily

from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-001")
resp = llm.invoke("talk about instant replay in baseball")
resp.content


# embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

embedder = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# https://ai.google.dev/api/embeddings#v1beta.TaskType
e = embedder.embed_query("Is instant replay a good thing in professional sports?", task_type="RETRIEVAL_QUERY")
type(e) # list
len(e) #768

# try with a list
texts = ["Instant replay is terrible", "We need more dog parks, here's why"]
e2 = embedder.embed_documents(texts, task_type="RETRIEVAL_DOCUMENT")
type(e2) #list
[len(tmp) for tmp in e2] # 768, 768