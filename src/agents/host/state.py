# agent/host/state.py
# from typing import TypedDict, Literal, Optional

# class HostState(TypedDict, total=False):
#     event: Literal["chat"]
#     text: str
#     forced: Optional[str]
#     next: Optional[str]
#     answer: Optional[str]
from typing import TypedDict, Literal, Optional, Any, Dict
from langgraph.prebuilt.chat_agent_executor import AgentState

class ChatState(AgentState, total=False):
    event: Literal["chat", "tool"]
    forced: Optional[str]
    next: Optional[str]
    answer: Optional[str]
    tool: Optional[str]
    tool_input: Optional[Any]
    tool_output: Optional[Any]
    metadata: Optional[Dict[str, Any]]