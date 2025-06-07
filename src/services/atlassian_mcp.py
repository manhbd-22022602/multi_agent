import asyncio
from functools import cache
from langchain_mcp_adapters.client import MultiServerMCPClient

# Singleton loader – chạy đúng 1 lần, cache kết quả
@cache
def _get_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "atlassian": {
                "transport": "streamable_http",
                "url": "http://localhost:8405/mcp",
            },
            # sau này thêm "github": {...}
        }
    )

async def load_atlassian_tools():
    """Return a dict {namespace: [Tool, …]} – cached after first run."""
    client = _get_client()
    return await client.get_tools()


# Sync helper – cho code không async (Streamlit, tests)
def load_atlassian_tools_sync():
    return asyncio.run(load_atlassian_tools())
