# agent/pm/pm.py
from __future__ import annotations
import logging
from langchain.tools import StructuredTool
from services.atlassian_mcp import load_atlassian_tools_sync
from services.github_mcp import load_github_tools_sync

logger = logging.getLogger(__name__)
tools_cache: dict[str, list[StructuredTool]] = {}

# PM Agent
class PMAgent:
    def __init__(self) -> None:
        pass
