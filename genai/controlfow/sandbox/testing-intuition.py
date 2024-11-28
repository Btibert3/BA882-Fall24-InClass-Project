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
# model = ChatVertexAI(model="gemini-1.5-flash", credentials=credentials, )  # can set temperature
model = ChatVertexAI(model="gemini-1.5-pro-001", credentials=credentials, )  # can set temperature

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


############################################## modified from the docs

from controlflow.orchestration.conditions import AnyComplete, MaxLLMCalls

@cf.flow
def dothething():
    result = cf.run_tasks(
        tasks=[cf.Task("write a poem about AI"), cf.Task("write a poem about ML")],
        run_until=AnyComplete() | MaxLLMCalls(10)
    )
    return result

x = dothething()


############################################## there is a efault agent in the background
# this is why running a task without an agent works
# improves ux, but abstracts away important context

cf.defaults.agent


###########################################

# create three agents
agent1 = cf.Agent(name="Agent 1")
agent2 = cf.Agent(name="Agent 2")
agent3 = cf.Agent(name="Agent 3")

# in dash, not as much info as I would have liked/hoped
cf.run(
    "Say hello to each other",
    instructions=(
        "Mark the task successful only when every "
        "agent has posted a message to the thread."
    ),
    agents=[agent1, agent2, agent3],
    # supply a turn strategy
    turn_strategy=cf.orchestration.turn_strategies.RoundRobin(),
)

hello_task = cf.Task(
    objective="The agents should talk to each other",
    instructions=(
        "Mark the task successful only when every "
        "agent has posted a message to the thread."
    ),
    agents=[agent1, agent2, agent3],
)

@cf.flow
def hello_flow():
    x = hello_task.run(
        turn_strategy=cf.orchestration.turn_strategies.RoundRobin(),
    )
    return x

hello_flow()

############################################## modified from docs, 

optimist = cf.Agent(
    name="Optimist",
    instructions="Always find the best in every situation.",
)

pessimist = cf.Agent(
    name="Pessimist",
    instructions="Always find the worst in every situation.",
)

task = cf.Task(
    objective="Debate world peace",
    agents=[optimist, pessimist],
    instructions=(
        "Mark the task successful once both agents have "
        "found something to agree on."
        "It is important that both agents contribute at least one response in the dbeate"
    )
)

@cf.flow
def debate_peace():
    x = task.run()
    return x

x = debate_peace()

#### need to ask on the forums why each agent isnt fired, single task but coordination is not obvious/working


##################################### parent task

parent_task = cf.Task("Create a greeting")

t1 = cf.Task("Choose a greeting word", parent=parent_task)
t2 = cf.Task("Add a friendly adjective", parent=parent_task, depends_on=[t1])
t3 = cf.Task("Construct the final greeting", parent=parent_task, depends_on=[t2])

result = parent_task.run()
print(result)



##################################### from examples

import sys
from controlflow import Agent, Task, flow

jerry = Agent(
    name="Jerry",
    description="The observational comedian and natural leader.",
    instructions="""
    You are Jerry from the show Seinfeld. You excel at observing the quirks of
    everyday life and making them amusing. You are rational, often serving as
    the voice of reason among your friends. Your objective is to moderate the
    conversation, ensuring it stays light and humorous while guiding it toward
    constructive ends.
    """,
)

george = Agent(
    name="George",
    description="The neurotic and insecure planner.",
    instructions="""
    You are George from the show Seinfeld. You are known for your neurotic
    tendencies, pessimism, and often self-sabotaging behavior. Despite these
    traits, you occasionally offer surprising wisdom. Your objective is to
    express doubts and concerns about the conversation topics, often envisioning
    the worst-case scenarios, adding a layer of humor through your exaggerated
    anxieties.
    """,
)

elaine = Agent(
    name="Elaine",
    description="The confident and independent thinker.",
    instructions="""
    You are Elaine from the show Seinfeld. You are bold, witty, and unafraid to
    challenge social norms. You often take a no-nonsense approach to issues but
    always with a comedic twist. Your objective is to question assumptions, push
    back against ideas you find absurd, and inject sharp humor into the
    conversation.
    """,
)

kramer = Agent(
    name="Kramer",
    description="The quirky and unpredictable idea generator.",
    instructions="""
    You are Kramer from the show Seinfeld. Known for your eccentricity and
    spontaneity, you often come up with bizarre yet creative ideas. Your
    unpredictable nature keeps everyone guessing what you'll do or say next.
    Your objective is to introduce unusual and imaginative ideas into the
    conversation, providing comic relief and unexpected insights.
    """,
)

newman = Agent(
    name="Newman",
    description="The antagonist and foil to Jerry.",
    instructions="""
    You are Newman from the show Seinfeld. You are Jerry's nemesis, often
    serving as a source of conflict and comic relief. Your objective is to
    challenge Jerry's ideas, disrupt the conversation, and introduce chaos and
    absurdity into the group dynamic.
    """,
)


@flow
def demo(topic: str):
    task = Task(
        "Discuss a topic",
        agents=[jerry, george, elaine, kramer, newman],
        completion_agents=[jerry],
        result_type=None,
        context=dict(topic=topic),
        instructions="Every agent should speak at least once. only one agent per turn. Keep responses 1-2 paragraphs max.",
    )
    task.run()

topic = "twitter renamed to X"
results = demo(topic)

## starts to work, but chokes on requests per minute quota (5, even with gemini and flash)

# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         topic = sys.argv[1]
#     else:
#         topic = "sandwiches"
    
#     print(f"Topic: {topic}")
#     demo(topic=topic)


