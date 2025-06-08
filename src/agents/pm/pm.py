from __future__ import annotations
from configs.config_loader import AVAILABLE_AGENTS, llm_local, llm_api

import logging
from typing import Dict, Any, Optional, TypedDict, Literal, List
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, START, END
from langchain.schema import SystemMessage, HumanMessage
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from services.atlassian_mcp import load_atlassian_tools
from services.github_mcp import load_github_tools

logger = logging.getLogger(__name__)

# Structured output model for planning
class StepList(BaseModel):
    steps: List[str] = Field(
        description="List of step-by-step actions for the request"
    )

# RoutingOutput to enforce delegation label
class RoutingOutput(BaseModel):
    label: str = Field(
        description="Label for tool choice: 'jira_read','jira_write','confluence_read','confluence_write','github','self_answer'"
    )

# PM state
class PMState(TypedDict, total=False):
    event:   Literal["chat", "tool_result"]
    text:    str                # user input or follow-up
    context_id: Optional[str]
    steps:   List[str]          # planned steps
    current: Optional[str]      # current step text
    outcome: Optional[str]      # routing outcome
    tool_result: Any            # raw tool response
    ask_user: Optional[str]     # missing info prompt
    answer: Optional[str]       # final response

tools_cache: dict[str, list[StructuredTool]] = {}

# PM Agent
class PMAgent:
    def __init__(self) -> None:
        self.AGENT_IDS = {
            'jira_read', 'jira_write', 'confluence_read',
            'confluence_write', 'github', 'self_answer'
        }
        self._graph = self._build_graph()
    
    def _match(self, state: PMState, hub_name: str) -> bool:
        current = state.get('current') or ""
        return hub_name.lower() in current.lower()

    def _build_graph(self) -> Any:
        sg = StateGraph(PMState)

        # planning node
        sg.add_node("planning", self._planning_node)

        # hubs
        for hub in ['jira_read', 'jira_write', 'confluence_read', 'confluence_write', 'github']:
            sg.add_node(hub, self._make_hub(hub))

        # self-answer
        sg.add_node("self_answer", self._self_answer_node)
        sg.add_node("ask_user_node", self._ask_user_node)

        # graph edges
        sg.add_edge(START, "planning")
        # after planning, iterate steps
        hubs = ["jira_read","jira_write","confluence_read","confluence_write","github","self_answer"]
        sg.add_conditional_edges(
            "planning",
            lambda s: [hub for hub in hubs if self._match(s, hub)]
        )

        # hubs return to END or ask_user
        for node in ['jira_read', 'jira_write', 'confluence_read', 'confluence_write', 'github', 'self_answer']:
            sg.add_conditional_edges(
                node,
                lambda s: s.get('outcome'),
                { 'need_more':'ask_user_node', 'done':END }
            )
        sg.add_edge('ask_user_node', END)

        return sg.compile()

    # planning: generate steps list
    async def _planning_node(self, state: PMState) -> PMState:
        system = SystemMessage(
            content="""
You are a project manager assistant. Break down the user's request into an ordered list of clear steps.
Return JSON only with a field 'steps', an array of step instructions."""
        )
        user = HumanMessage(content=state['text'])
        llm = llm_local().with_structured_output(StepList)
        result = await llm.ainvoke([system, user])
        state['steps'] = result.steps
        # set current to first step for routing
        state['current'] = state['steps'][0] if result.steps else None
        return state

    # make hub function
    def _make_hub(self, hub_name: str):
        async def _hub(state: PMState) -> PMState:
            # select tool
            tools = await self._load_tools()[hub_name]
            llm = llm_local()
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"Select the best tool for: {state['current']}. Available: {list(tools.keys())}"),
                ("user", state['current'])
            ])
            choice = await llm.arun(prompt.format_prompt().to_messages())
            selected = tools.get(choice.strip(), list(tools.values())[0])
            try:
                args = {'query': state['current']} if 'read' in hub_name else {'jql': state['current']}
                result = await selected.arun(**args)
                state['tool_result'] = result
                state['outcome'] = 'done'
            except Exception as e:
                state['ask_user'] = str(e)
                state['outcome'] = 'need_more'
            return state
        return _hub

    # self-answer
    async def _self_answer_node(self, state: PMState) -> PMState:
        system = SystemMessage(content="You are a helpful PM assistant. Answer the request:")
        user = HumanMessage(content=state['current'])
        resp = await llm_api().ainvoke([system, user])
        state['answer'] = resp.content.strip()
        state['outcome'] = 'done'
        return state

    # ask user
    async def _ask_user_node(self, state: PMState) -> PMState:
        state['answer'] = state.get('ask_user') or 'Additional info required.'
        return state

    @staticmethod
    async def _load_tools() -> dict[str, list[StructuredTool]]:
        global tools_cache
        if tools_cache:
            return tools_cache

        all_tools = await load_atlassian_tools()
        github_tools = await load_github_tools()

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
            "jira_read": jira_read,
            "jira_write": jira_write,
            "confluence_read": confluence_read,
            "confluence_write": confluence_write,
            "github": github_tools,
        }
        return tools_cache

    async def run(self, state: PMState) -> PMState:
        return await self._graph.ainvoke(state)
