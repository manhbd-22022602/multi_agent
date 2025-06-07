import os
from dotenv import load_dotenv

from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from github_mcp import load_github_tools, load_github_tools_sync
from atlassian_mcp import load_atlassian_tools, load_atlassian_tools_sync

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

# Set key to environment so LangChain can auto-pick up
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

# Instantiate LLM model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

tools = load_github_tools_sync() + load_atlassian_tools_sync()
print("Loaded tools:", tools)
agent = create_react_agent(llm, tools)
response = agent.invoke({"messages": "Bạn có thể sử dụng các tools nào? Của các bộ công cụ nào?"})
print(response)