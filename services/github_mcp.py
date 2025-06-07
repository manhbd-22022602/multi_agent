import os, asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
GITHUB_PAT = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]

# ------------- ASYNC -------------
async def load_github_tools():
    """Trả về list Tool từ GitHub MCP Server (stdio)."""
    server_params = StdioServerParameters(
        command="docker",
        args=[
            "run", "-i", "--rm",
            "-e", f"GITHUB_PERSONAL_ACCESS_TOKEN={GITHUB_PAT}",
            "mcp/github-mcp-server:latest"
        ],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            return tools

# ------------- SYNC tiện dùng cho Streamlit -------------
def load_github_tools_sync():
    return asyncio.run(load_github_tools())
