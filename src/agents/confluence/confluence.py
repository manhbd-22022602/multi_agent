# agent/jira/jira.py
from __future__ import annotations
import logging
from langchain.tools import StructuredTool
from services.atlassian_mcp import load_atlassian_tools_sync

logger = logging.getLogger(__name__)
tools_cache: dict[str, list[StructuredTool]] = {}

# Confluence Agent
class ConfluenceAgent:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _load_tools() -> dict[str, list[StructuredTool]]:
        global tools_cache
        if tools_cache:
            return tools_cache

        all_tools = load_atlassian_tools_sync()

        # Phân nhóm các tools
        confluence_read = [
            t for t in all_tools
            if t.name.startswith((
                "confluence_get",
                "confluence_search",
            ))
        ]

        confluence_write = [
            t for t in all_tools
            if t.name.startswith((
                "confluence_create",
                "confluence_update",
                "confluence_delete",
                "confluence_add_label",
                "confluence_add_comment",
            ))
        ]

        tools_cache = {
            "confluence_read": confluence_read,
            "confluence_write": confluence_write,
        }
        return tools_cache