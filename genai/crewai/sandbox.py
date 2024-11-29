# pip install crewai crewai-tools

# from langchain_google_genai import ChatGoogleGenerativeAI
from crewai import Agent, Task, Crew
from crewai_tools import ScrapeWebsiteTool
import requests
import os

import requests
from bs4 import BeautifulSoup





############################### basics from datacamp article

# Initialize the tool, potentially passing the session
tool = ScrapeWebsiteTool(website_url='https://en.wikipedia.org/wiki/Artificial_intelligence')  

# Extract the text
text = tool.run()
print(text)


############################### a little more advanced

# llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-001")

# uses litellm - https://docs.litellm.ai/docs/providers/vertex
os.environ["VERTEX_PROJECT"] = "btibert-ba882-fall24"
os.environ["VERTEX_LOCATION"] = "us-central1"


summarizer = Agent(
    role='Summarizer',
    goal="For a provided text input {input}, summarize the text succinctly while retaining the core pieces of information.  Use no more than three paragraphs",
    backstory='You are an expert and succintly reading text documents and summarizing them for end users',
    verbose=True,
    llm="gemini-1.5-pro-001",
    allow_delegation=False
)

task = Task(
    description='Summarize the text',
    agent=summarizer,
    expected_output='A single paragraph summary that also includes five succinct key facts from the text',
)

# need to pass in as lists
crew = Crew(agents=[summarizer], tasks=[task])

def fetch_paragraph_texts(url):
    try:
        # Fetch the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract text from all <p> tags
        paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]

        # Join paragraphs into a single text (optional)
        return "\n\n".join(paragraphs)
    except requests.exceptions.RequestException as e:
        return f"Error fetching the webpage: {e}"

url = "https://www.edweek.org/policy-politics/a-bill-to-kill-the-education-department-is-already-filed-heres-what-it-says/2024/11"
content = fetch_paragraph_texts(url)
summary = crew.kickoff(inputs=dict(input=content))

print(summary.raw)