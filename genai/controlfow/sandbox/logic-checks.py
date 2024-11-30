# for me, start to test the mental model/setup

import controlflow as cf # info warning, default is open ai is aggressive
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2.service_account import Credentials
from prefect_gcp import GcpCredentials
from langchain_google_vertexai import ChatVertexAI

# will be required if logic is on the box that prefect is managing
gcp_credentials_block = GcpCredentials.load("ba882-fall24-etl-sa")
service_account_json_str = gcp_credentials_block.service_account_info.get_secret_value()
credentials = Credentials.from_service_account_info(service_account_json_str)

# set the model as the default
model = ChatVertexAI(model="gemini-1.5-pro-001", credentials=credentials)
cf.defaults.model = model

############################################ Example 1: summary rewriter





############################################ Example 2: categorizer

# NOTES:  use variable for MD within prefect
#         get yesterday, if posts, new summary, LLM judge compare, write both to MD with winner flag
#         from list of categories (5+), pick categories for post, check agreement
#         frame both from Marketing team asking data team for help 





