import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2.service_account import Credentials

from prefect_gcp import GcpCredentials
gcp_credentials_block = GcpCredentials.load("ba882-fall24-etl-sa")

service_account_json_str = gcp_credentials_block.service_account_info.get_secret_value()
credentials = Credentials.from_service_account_info(service_account_json_str)

from langchain_google_vertexai import ChatVertexAI
model = ChatVertexAI(model="gemini-1.5-flash", credentials=credentials)

import controlflow as cf 


cf.defaults.model = model



emails = [
    "Hello, I need an update on the project status.",
    "Subject: Exclusive offer just for you!",
    "Urgent: Project deadline moved up by one week.",
]


reply = cf.run(
    "Write a polite reply to an email",
    context=dict(email=emails[0])
)

print(reply)

# # the job
# if __name__ == "__main__":
#     etl_flow()


## learnings
## set the default agent
## doesnt appear to log to prefect, if thats the case, no need for block, just define
## could be used in a function, potentially, as if it were an endpoint that could be engaged via something like slack/streamlit






# import controlflow as cf

# agent = cf.Agent(model=model)

# subprocess.Popen(['prefect', 'server', 'stop'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
