# test a combination of things (prefect and controlflow)

import requests
from bs4 import BeautifulSoup
import html

import controlflow as cf
from prefect import flow, task

from pydantic import BaseModel

import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2.service_account import Credentials

from prefect_gcp import GcpCredentials
gcp_credentials_block = GcpCredentials.load("ba882-fall24-etl-sa")

service_account_json_str = gcp_credentials_block.service_account_info.get_secret_value()
credentials = Credentials.from_service_account_info(service_account_json_str)

from langchain_google_vertexai import ChatVertexAI
model = ChatVertexAI(model="gemini-1.5-flash", credentials=credentials, )  # can set temperature

cf.defaults.model = model


################## this is a task that runs by itself
poem = cf.run(
    "Write a poem about AI",
    instructions="Write only two lines, and end the first line with `not evil`",
)

print(poem)


################## create a task directly
## this fits the mental model for me

task = cf.Task(
    objective="Write a poem about the provided topic",
    instructions="Write four lines that rhyme",
    context={"topic": "Boston Bruins"}
)

result = task.run()
print(result)


############################################ summarize an article and grab entities

url = "https://www.boston.com/news/local-news/2024/11/27/as-free-college-drives-up-enrollment-community-college-professors-want-raises/?p1=hp_featurestack"
resp = requests.get(url)
soup = BeautifulSoup(resp.text, 'html.parser')
body = soup.body.get_text(separator=" ", strip=True)
body = html.unescape(body)

from pydantic import BaseModel
from typing import List, Dict

class Entity(BaseModel):
    type: str
    value: str

class TextAnalysisResult(BaseModel):
    summary: str
    entities: List[Entity]

summarizer = cf.Agent(
    name="Article Summarizer",
    instructions="For a given input text, summarize the article in five bullet points or less. You must return bullets.",
    model = model
)

ner = cf.Agent(
    name="Enttiy extractor",
    instructions="For a given input text, extract entities.  This should be the type of entity and its value.",
    model = model
)

article_summary = cf.Task(
    objective="Summarize and Extract entities",
    result_type = TextAnalysisResult,
    context = dict(article=body), 
    agents=[summarizer, ner]
)

parsed_article = article_summary.run()
parsed_article.model_dump()
#^^^^^ does what I expected, 
# learnings: https://prefect-community.slack.com/archives/C079VLLH5D3/p1732553949663869?thread_ts=1732254729.604839&cid=C079VLLH5D3
#            



############################################ more advanced
# resource: https://controlflow.ai/patterns/running-tasks
# for some reason its under tasks where it talks about agents and coordinatoin
# https://controlflow.ai/patterns/running-tasks#managing-the-agentic-loop

summary_agent = cf.Agent(name="Article Summarizer")
critic = cf.Agent(name="Critic")

task2 = cf.Task(
    objective='Generate a well written summary of the article, and then critque its quality', 
    agents=[summary_agent, critic],
    context = dict(article=body), 
)

task2_results = task2.run(
    turn_strategy=cf.orchestration.turn_strategies.RoundRobin()
)

print(task2_results)


optimist = cf.Agent(name="Optimist")
pessimist = cf.Agent(name="Pessimist", model=model)
moderator = cf.Agent(name="Moderator")

mod_results = cf.run(
    "Debate the meaning of life",
    instructions='Give each agent at least three chances to speak.',
    agents=[moderator, optimist, pessimist],
    completion_agents=[moderator],
    turn_strategy=cf.orchestration.turn_strategies.Moderated(moderator=moderator),
)


# from controlflow.orchestration import orchestrator
# orchestrator.