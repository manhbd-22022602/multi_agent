from fastmcp import FastMCP
from agents.jira.graph import graph as jira_agent
from agents.confluence.graph import graph as confluence_agent
from services.qodo_cover_tool import create_unit_test as _create_unit_test

mcp = FastMCP("GitHub Copilot Agent Server")

# @mcp.tool(
#     name="jira_agent_handler",
#     description=(
#         "Handles Jira-related tasks such as:\n"
#         "- Counting the number of issues in a Jira project\n"
#         "- Reading the content of a task or Epic\n"
#         "- Updating the status of a ticket or adding a comment\n"
#         "- Summarizing content from a Jira documentation page\n\n"
#         "This tool accepts a single JSON object with an `message` field containing the natural language request.\n"
#         "The tool automatically determines which sub-action to invoke inside the Jira agent.\n\n"
#         "### Args:\n"
#         "- message (dict): JSON object with the form `{ \"message\": \"<your Jira-related question>\" }`.\n\n"
#         "### Returns:\n"
#         "- A JSON object containing the result of the requested Jira operation, such as a count, issue details, update status, or summary."
#     )
# )
# async def handle_jira_agent(message: dict):
#     print(message)
#     response = await jira_agent.invoke(message)
#     return response

# @mcp.tool(
#     name="confluence_agent_handler",
#     description=(
#         "Handles Confluence document-related tasks such as:\n"
#         "- Searching for content within Confluence spaces\n"
#         "- Reading the content of a specific page\n"
#         "- Creating or updating a Confluence documentation page\n\n"
#         "This tool accepts a single JSON object with an `message` field describing the user query in natural language.\n"
#         "The tool routes the request to the appropriate function inside the Confluence agent.\n\n"
#         "### Args:\n"
#         "- message (dict): JSON object with the form `{ \"message\": \"<your Confluence-related question>\" }`.\n\n"
#         "### Returns:\n"
#         "- A JSON object with the result of the requested Confluence operation, such as a page's content, summary, or confirmation of a successful update or creation."
#     )
# )
# async def handle_confluence_agent(message: dict):
#     response = await confluence_agent.invoke(message)
#     return response

CREATE_UNIT_TEST_DESC = _create_unit_test.description
@mcp.tool(name="create_unit_test", description=CREATE_UNIT_TEST_DESC)
async def create_unit_test(args: dict) -> str:
    return _create_unit_test.invoke(input=args)

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8408)