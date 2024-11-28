# an agent that fires on an event to prefect 

import controlflow as cf
from prefect import flow, task

import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2.service_account import Credentials

from prefect_gcp import GcpCredentials
gcp_credentials_block = GcpCredentials.load("ba882-fall24-etl-sa")

service_account_json_str = gcp_credentials_block.service_account_info.get_secret_value()
credentials = Credentials.from_service_account_info(service_account_json_str)

from langchain_google_vertexai import ChatVertexAI
model = ChatVertexAI(model="gemini-1.5-flash", credentials=credentials)

cf.defaults.model = model

@cf.flow
def my_flow(x=5):
    y = cf.run('Add 5 to the number', result_type=int, context=dict(x=x))
    z = cf.run('Multiply the result by 2', result_type=int)
    return z

@flow
def agent_example1():
    resp = my_flow()
    print(resp)

# the job
if __name__ == "__main__":
    agent_example1()
