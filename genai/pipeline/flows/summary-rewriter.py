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
print(f"number of posts found: {len(posts)}")


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
    Evaluate the draft summary. Compare the summary generated by your writer to the original body text and determine if it 
    meets your standards at summarizing the original body text.
    """
)

judge = cf.Agent(
    name="Judge",
    description="An AI agent that acts as an judge",
    instructions=""" 
    Comparing two entries to a reference and determining and vote for one of the entires.  
    Your selection should choose the submission that best summarizes the original text in a single paragraph.
    """
)


@cf.flow
def summary_eval(body:str):
    # the summary task
    summary_task = cf.Task(
        objective="Summarize a body of text",
        instructions =""" 
        For the body text, summarize the text in a single paragraph.
        """,
        agents=[writer],
        result_type=str,
        context={"text": body}
    )

    summary = summary_task.run(max_llm_calls=3)

    # the evaluation task
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


@cf.flow
def summarizer_flow():

    # if len == 0
    if len(posts) == 0:
        print("No posts to process")
        return {}
    
    # flatten to a list of dictionaries
    posts_list = posts.to_dict(orient="records")

    # process records
    with cf.Flow():
        votes = []
        for entry in posts_list:
            print(f"processing post id: {entry.get('id')}")
            body_text = entry.get('content_text')
            output = summary_eval(body=body_text)
            vote = cf.run("Vote for the best summary, you must choose one of the two summaries", 
                agents=[judge], 
                context=dict(body=body_text, 
                            summary1=output[0], 
                            summary2=entry.get('summary')),
                result_type=['summary1', 'summary2']
            )
            votes.append(vote)

# the job
if __name__ == "__main__":
    summarizer_flow()


        
