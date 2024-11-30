# imports
import requests
import duckdb
from prefect import flow, task
import controlflow as cf 
from prefect_gcp import GcpCredentials
from prefect.variables import Variable
from google.oauth2.service_account import Credentials
from langchain_google_vertexai import ChatVertexAI

# will be required if logic is on the box that prefect is managing
gcp_credentials_block = GcpCredentials.load("ba882-fall24-etl-sa")
service_account_json_str = gcp_credentials_block.service_account_info.get_secret_value()
credentials = Credentials.from_service_account_info(service_account_json_str)

# set the model as the default
model = ChatVertexAI(model="gemini-1.5-pro-001", credentials=credentials)
cf.defaults.model = model

# get the variable
md_token = Variable.get("md_token").get("token")

# connect to duckdb
md = duckdb.connect(f'md:?motherduck_token={md_token}') 

# get the posts from the last day
sql = "select * from awsblogs.stage.posts where strftime(published, '%Y-%m-%d') = strftime(CURRENT_DATE - INTERVAL 1 DAY, '%Y-%m-%d');"
posts = md.sql(sql).df()

@cf.flow
def summarize_text(body:str):

    # create the Agents
    writer = cf.Agent(
        name="Blog Post Summarizer",
        description="An AI agent that summarizes text content",
        instructions=""" 
        You are an expert at summarizing passages of text.  
        You retain the core information and are able to succintly describe the text in a single paragraph.
        """
    )

    editor = cf.Agent(
        name="Editor",
        description="An AI agent that acts as an editor",
        instructions=""" 
        You are an expert editor.  You are capable of reviewing the summaries written by your staff
        and determining if they are of high quality.  
        """
    )

    # parent task
    with cf.Task(
            "Summarize the body text into a single paragraph summary",
            agents=[editor],
        ) as main_task:

        while main_task.is_incomplete():


            # create the tasks
            summary_task = cf.Task(
                objective="Summarize a body of text",
                instructions =""" 
                For the body text, summarize the text into a single paragraph. 
                """,
                context={"text": body},
                agents=[writer],
                result_type=str
            )

            summary = summary_task.run()

            eval_task = cf.Task(
                objective= """
                Determine if the summary effective at describing the text succinctly in a single paragraph.
                If the summary 
                """,
                instructions = """
                Evaluate the draft summary. Compare the summary generated by your writer and determine if it 
                meets the following requirements:
                - a single paragraph
                - the summary should identify the core theme of the body of text
                Your objective is to determine if this meets your requirements.  If it does 
                mark the main task as successful, otherwise ask the writer agent to attempt again, at which point you provide detailed feedback in the form
                of bullet points in order to help the writer improve their submission.
                """,
                agents=[editor],
                depends_on=[summary_task],
                context={"text": body, "summary": summary},
                tools=[main_task.get_success_tool()]
            )

            evals = eval_task.run()


    return (summary)


# lets see how it goes
tmp = summarize_text(body=txt)



# create the Agents
writer = cf.Agent(
    name="Blog Post Summarizer",
    description="An AI agent that summarizes text content",
    instructions=""" 
    You are an expert at summarizing passages of text.  
    You retain the core information and are able to succintly describe the text in a single paragraph.
    """
)

editor = cf.Agent(
    name="Editor",
    description="An AI agent that acts as an editor",
    instructions=""" 
    Evaluate the draft summary. Compare the summary generated by your writer and determine if it 
    meets the following requirements:
    - a single paragraph
    - the summary should identify the core theme of the body of text
    Your objective is to determine if this meets your requirements.  If it does 
    mark the main task as successful, otherwise ask the writer agent to attempt again, at which point you provide detailed feedback in the form
    of bullet points in order to help the writer improve their submission.
    """
)





@flow
def demo(body: str):
    task = cf.Task(
        "For a body text, create an effective single paragraph summary.",
        agents=[writer, editor],
        completion_agents=[editor],
        result_type=str,
        context=dict(text=body),
        instructions="The writer agent should attempt to summary the body text.  The editor will determine if it meets the requirements and provides feedback for another attempt.",

    )
    task.run()

tmp = demo(body=txt)






@cf.flow
def summary_eval(body:str):
    # create the tasks
    summary_task = cf.Task(
        objective="Summarize a body of text",
        instructions =""" 
        For the body text, summarize the text into a single paragraph. 
        """,
        agents=[writer],
        result_type=str,
        context={"text": body}
    )

    summary = summary_task.run(max_llm_calls=3)

    eval_task = cf.Task(
        objective= """
        Determine if the summary effective at describing the text succinctly in a single paragraph.
        If the summary 
        """,
        instructions = """
        Evaluate the draft summary. Compare the summary generated by your writer to the original text and determine if it 
        meets the following requirements:
        - a single paragraph
        - the summary should identify the core theme of the body of text
        Your objective is to determine if this meets your requirements.  If it doesn't, ask the writer agent to attempt again, at which point you provide detailed feedback in the form
        of bullet points in order to help the writer improve their submission.
        """,
        agents=[editor],
        context={"text": body, "summary": summary}
    )

    evals =  eval_task.run(max_llm_calls=3)

    return (summary, evals)



tmp = summary_eval(body=txt)