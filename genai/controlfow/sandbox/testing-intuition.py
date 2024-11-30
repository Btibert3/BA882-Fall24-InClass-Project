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
# model = ChatVertexAI(model="gemini-1.5-pro-001", credentials=credentials, )  # can set temperature
model = ChatVertexAI(model="gemini-1.0-pro", credentials=credentials, )  # can set temperature


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

model = ChatVertexAI(model="gemini-1.5-pro-001", credentials=credentials, )  # can set temperature
# model = ChatVertexAI(model="gemini-1.0-pro", credentials=credentials, )  # can set temperature
cf.defaults.model = model

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

topic = "instant replay in Major league baseball"
results = demo(topic)

## starts to work, but chokes on requests per minute quota (5, even with gemini and flash)
## lesser model pro 1, doesn't flip from Jerry, but odd that I just tried twice with 1.5 pro and no quota limit but likely inside tolerance
## add odd it shows 5 on dashboard but 300 https://cloud.google.com/vertex-ai/generative-ai/docs/quotas
## submitted request to 100, not even 300, described why, odd I also had to give a phone number
## it creates a GCP case -> which you can see on the tab, and it was approved pretty quickly
## worth noting is that the logs on cloud align to what I would have expected, but not shown in other examples above.
## still dont quite understanding where the prompt is being logged, I expected to see details on how this is being orchesterated

# if __name__ == "__main__":
#     if len(sys.argv) > 1:
#         topic = sys.argv[1]
#     else:
#         topic = "sandwiches"
    
#     print(f"Topic: {topic}")
#     demo(topic=topic)


###################################### call routing example
## 

import random
import controlflow as cf

DEPARTMENTS = [
    "Sales",
    "Support",
    "Billing",
    "Returns",
]

@cf.flow
def routing_flow():
    target_department = random.choice(DEPARTMENTS)

    print(f"\n---\nThe target department is: {target_department}\n---\n")

    customer = cf.Agent(
        name="Customer",
        instructions=f"""
            You are training customer reps by pretending to be a customer
            calling into a call center. You need to be routed to the
            {target_department} department. Come up with a good backstory.
            """,
    )

    trainee = cf.Agent(
        name="Trainee",
        instructions=""",
            You are a trainee customer service representative. You need to
            listen to the customer's story and route them to the correct
            department. Note that the customer is another agent training you.
            """,
    )

    with cf.Task(
        "Route the customer to the correct department.",
        agents=[trainee],
        result_type=DEPARTMENTS,
    ) as main_task:
        
        while main_task.is_incomplete():
            
            cf.run(
                "Talk to the trainee.",
                instructions=(
                    "Post a message to talk. In order to help the trainee "
                    "learn, don't be direct about the department you want. "
                    "Instead, share a story that will let them practice. "
                    "After you speak, mark this task as complete."
                ),
                agents=[customer],
                result_type=None
            )

            cf.run(
                "Talk to the customer.",
                instructions=(
                    "Post a message to talk. Ask questions to learn more "
                    "about the customer. After you speak, mark this task as "
                    "complete. When you have enough information, use the main "
                    "task tool to route the customer to the correct department."
                ),
                agents=[trainee],
                result_type=None,
                tools=[main_task.get_success_tool()]
            )
    
    if main_task.result == target_department:
        print("Success! The customer was routed to the correct department.")
    else:
        print(f"Failed. The customer was routed to the wrong department. "
              f"The correct department was {target_department}.")


## works after the quota increase, but saw the following
## some empty LLM calls, repeated mark of tasks successful, seemingly a restart of the convo, and end.  



##################################### language tutor from docs

from pydantic import BaseModel

class Lesson(BaseModel):
    topic: str
    content: str
    exercises: list[str]

def language_learning_session(language: str) -> None:
    tutor = cf.Agent(
        name="Tutor",
        instructions="""
        You are a friendly and encouraging language tutor. Your goal is to create an 
        engaging and supportive learning environment. Always maintain a warm tone, 
        offer praise for efforts, and provide gentle corrections. Adapt your teaching 
        style to the user's needs and pace. Use casual language to keep the 
        conversation light and fun. When working through exercises:
        - Present one exercise at a time.
        - Provide hints if the user is struggling.
        - Offer the correct answer if the user can't solve it after a few attempts.
        - Use encouraging language throughout the process.
        """
    )

    @cf.flow(default_agent=tutor)
    def learning_flow():
        cf.run(
            f"Greet the user, learn their name,and introduce the {language} learning session",
            interactive=True
        )

        while True:
            lesson = cf.run(
                "Create a fun and engaging language lesson",
                result_type=Lesson
            )

            cf.run(
                "Present the lesson content to the user in an interactive and engaging way",
                interactive=True,
                context={"lesson": lesson}
            )

            for exercise in lesson.exercises:
                cf.run(
                    "Work through the exercise with the user",
                    interactive=True,
                    context={"exercise": exercise}
                )

            continue_learning = cf.run(
                "Check if the user wants to continue learning",
                result_type=bool,
                interactive=True
            )

            if not continue_learning:
                break

        cf.run(
            "Summarize the learning session and provide encouragement",
            interactive=True
        )

    learning_flow()

# Example usage
language_learning_session("Spanish")

####### ^^^^^ gets into a loop again, interactive is odd anyway, but the graph execution isn't great
######        confirms that this is good for pipelines (build a report, not interactive)


################################################# write markdown

