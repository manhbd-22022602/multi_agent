# agent/jira/jira.py
from __future__ import annotations
import logging
from langchain.tools import StructuredTool
from services.atlassian_mcp import load_atlassian_tools_sync

logger = logging.getLogger(__name__)
tools_cache: dict[str, list[StructuredTool]] = {}

# Jira Agent
class JiraAgent:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _load_tools() -> dict[str, list[StructuredTool]]:
        global tools_cache
        if tools_cache:
            return tools_cache

        all_tools = load_atlassian_tools_sync()

        # Phân nhóm các tools
        jira_read = [
            t for t in all_tools
            if t.name.startswith((
                "jira_get",
                "jira_search",
                "jira_search_fields",
                "jira_download_attachments",
                "jira_batch_get_changelogs",
                "jira_get_user_profile",
            ))
        ]

        jira_write = [
            t for t in all_tools
            if t.name.startswith((
                "jira_create",
                "jira_update",
                "jira_delete",
                "jira_batch_create",
                "jira_add_comment",
                "jira_transition",
                "jira_add_worklog",
                "jira_link_to_epic",
                "jira_create_sprint",
                "jira_update_sprint",
                "jira_create_issue_link",
                "jira_remove_issue_link",
            ))
        ]

        tools_cache = {
            "jira_read": jira_read,
            "jira_write": jira_write
        }
        return tools_cache
