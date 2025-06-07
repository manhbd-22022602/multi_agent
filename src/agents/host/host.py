# agent/host/host.py
from __future__ import annotations
from configs.config_loader import AVAILABLE_AGENTS, llm_local, llm_api

import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from typing import Dict, Any, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain.schema import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
# Định nghĩa RoutingOutput để ép LLM trả về nhãn agent
class RoutingOutput(BaseModel):
    label: str = Field(
        description="Agent ID cần gọi. Phải là một trong: 'pm', 'dev', 'qa', 'docu', 'report', 'none'. Nếu không phù hợp, trả về 'none'."
    )

# HostAgent sub-graph
class HostAgent:
    def __init__(self) -> None:
        self.AGENT_IDS = set(AVAILABLE_AGENTS.values())

    # node implementations
    def rule_based(self, state: Dict[str, Any]) -> Dict[str, Any]:
        forced = state.get("forced")
        return {"next": forced} if self.forced_is_valid(forced) else {}

    async def llm_select(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agent = await self._llm_route(state["text"])
        return {"next": agent} if agent else {}

    async def finalize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Chỉ chạy khi KHÔNG có `next`
        """Gọi LLM để tự trả lời user nếu không xác định được Agent phù hợp."""
        if llm_api is None:
            return {
                "answer": "Host: Mình đã nhận câu hỏi và sẽ phản hồi sớm nhé!"
            }

        system = SystemMessage(
            content="Bạn là một trợ lý thân thiện. Hãy trả lời câu hỏi của người dùng một cách ngắn gọn, rõ ràng và hữu ích."
        )
        user = HumanMessage(content=state["text"])

        response = await llm_api.ainvoke([system, user])

        return {
            "answer": response.content.strip()
        }
    
    # helper methods
    def forced_is_valid(self, tag: Optional[str]) -> bool:
        return (tag in self.AGENT_IDS) or (tag == "none")

    async def _llm_route(self, text: str, attempts=5) -> Optional[str]:
        if llm_local is None:
            return None

        structured_llm = llm_local.with_structured_output(RoutingOutput)

        system = SystemMessage(
            content=(
                "You are the “Routing Module” for an IT Project Management assistant. "
                "Your job is to read a user’s free­form input and choose exactly one of these six labels:\n\n"
                "- pm – Project Manager (task planning, prioritization, resource allocation)\n"
                "- dev – Developer (writing code, technical design, debugging)\n"
                "- qa – QA Engineer (test cases, quality checks, bug reports)\n"
                "- docu – Documentation (writing specs, user guides, API docs)\n"
                "- report – Reporting (status updates, metrics, summaries)\n"
                "- none – Anything outside IT project management scope\n\n"
                "Rules:\n\n"
                "1. Only classify inputs that clearly belong to IT project management activities.\n" 
                "2. If the question is general trivia, small talk, or any non-PM/Dev/QA/Docu/Report topic, return none.\n"
                "3. Output must be valid JSON only, with exactly one field called `label`. Do not output any extra text.\n"
                "4. Use lowercase labels exactly as shown.\n\n"

                "Output format (no deviations!):\n\n" 
                "```json"
                "{'label':'<pm|dev|qa|docu|report|none>'}"
                "```"
            )
        )

        user = HumanMessage(content=text)

        # Thử lại nhiều lần nếu LLM trả về kết quả không hợp lệ
        for attempt in range(attempts):
            try:
                result: RoutingOutput = await structured_llm.ainvoke([system, user])
                label = result.label.strip().lower()
                logger.info("Prompt: %s -> Result: %s", [system, user], result)
                if self.forced_is_valid(label):
                    return label if label in self.AGENT_IDS else None
                else:
                    logger.info("[Host] Attempt %d: Invalid label -> %s", attempt+1, label)

            except Exception as e:
                logger.info("[Host] LLM routing failed at attempt %d: %s", attempt + 1, e)
                return None

        return None