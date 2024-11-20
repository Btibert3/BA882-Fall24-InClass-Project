# pip install controlflow
# pip install langchain-google-vertexai
# pip install prefect-gcp
# pip install "google-cloud-aiplatform>=1.64"

from prefect_gcp import GcpCredentials
gcp_credentials_block = GcpCredentials.load("ba882-fall24-etl-sa")

from google.oauth2.service_account import Credentials
import json

service_account_json_str = gcp_credentials_block.service_account_info.get_secret_value()
credentials = Credentials.from_service_account_info(service_account_json_str)

import controlflow as cf
from langchain_google_vertexai import ChatVertexAI

########### ^^ ignore

import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2.service_account import Credentials

from prefect_gcp import GcpCredentials
gcp_credentials_block = GcpCredentials.load("ba882-fall24-etl-sa")

service_account_json_str = gcp_credentials_block.service_account_info.get_secret_value()
credentials = Credentials.from_service_account_info(service_account_json_str)

from langchain_google_vertexai import ChatVertexAI
model = ChatVertexAI(model="gemini-1.5-flash", credentials=credentials)

import controlflow as cf # info warning, default is open ai is aggressive
agent = cf.Agent(model=model)

classifier = cf.Agent(
    name="yes or no",
    model = model,
    instructions="You have a single task.  reply simply with yes or no.  Your response is a single word, yes, or no.",
)

classifications = cf.run(
    'Flip a coin',
    result_type=['yes', 'no'],
    agents=[classifier],
)


project_id = "btibert-ba882-fall24"   
region_id = "us-central1"
vertexai.init(project=project_id, location=region_id, credentials=credentials)

# model = GenerativeModel("gemini-1.5-pro-001")






import controlflow as cf

agent = cf.Agent(model=model)


