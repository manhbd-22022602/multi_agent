# agent/Host/host.py
from __future__ import annotations
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from typing import Dict, Any, Optional, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langchain.schema import SystemMessage, HumanMessage
from configs.settings import AVAILABLE_AGENTS, LLM
from pydantic import BaseModel, Field

# Định nghĩa RoutingOutput để ép LLM trả về nhãn agent
class RoutingOutput(BaseModel):
    label: str = Field(
        description="Agent ID cần gọi. Phải là một trong: 'pm', 'dev', 'qa', 'docu', 'report'. Nếu không phù hợp, trả về 'none'."
    )

# Định nghĩa State cho Host Agent
class HostState(TypedDict, total=False):
    event:   Literal["chat"]
    text:    str
    forced:  Optional[str]
    next:    Optional[str]
    answer:  Optional[str]

# Khởi tạo LLM
llm_client = None
if LLM.startswith("gemini"):
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm_client = ChatGoogleGenerativeAI(model=LLM, temperature=0)

# HostAgent sub-graph
class HostAgent:
    def __init__(self) -> None:
        sg = StateGraph(HostState)

        sg.add_node("rule_based", self._rule_based)
        sg.add_node("llm_select", self._llm_select)
        sg.add_node("finalize",   self._finalize)

        sg.add_edge(START, "rule_based")

        # RULE-BASED: nếu đã có next  ⟹ END, ngược lại ⟹ llm_select
        sg.add_conditional_edges(
            "rule_based",
            lambda s: "exit" if "next" in s else "cont",
            {"exit": END, "cont": "llm_select"},
        )

        # LLM-SELECT: nếu đã có next ⟹ END, ngược lại ⟹ finalize
        sg.add_conditional_edges(
            "llm_select",
            lambda s: "exit" if "next" in s else "cont",
            {"exit": END, "cont": "finalize"},
        )

        sg.add_edge("finalize", END)
        self._graph = sg.compile()
        
        self.AGENT_IDS = set(AVAILABLE_AGENTS.values())

    # public entry
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return await self._graph.ainvoke(state)

    # node implementations
    def _rule_based(self, state: Dict[str, Any]) -> Dict[str, Any]:
        forced = state.get("forced")
        return {"next": forced} if self._forced_is_valid(forced) else {}

    async def _llm_select(self, state: Dict[str, Any]) -> Dict[str, Any]:
        agent = await self._llm_route(state["text"])
        return {"next": agent} if agent else {}

    async def _finalize(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Chỉ chạy khi KHÔNG có `next`
        """Gọi LLM để tự trả lời user nếu không xác định được Agent phù hợp."""
        if llm_client is None:
            return {
                "answer": "Host: Mình đã nhận câu hỏi và sẽ phản hồi sớm nhé!"
            }

        system = SystemMessage(
            content="Bạn là một trợ lý thân thiện. Hãy trả lời câu hỏi của người dùng một cách ngắn gọn, rõ ràng và hữu ích."
        )
        user = HumanMessage(content=state["text"])

        response = await llm_client.ainvoke([system, user])

        return {
            "answer": response.content.strip()
        }
    
    # helper methods
    def _forced_is_valid(self, tag: Optional[str]) -> bool:
        return tag in self.AGENT_IDS

    async def _llm_route(self, text: str) -> Optional[str]:
        if llm_client is None:
            return None
        
        structured_llm = llm_client.with_structured_output(RoutingOutput)

        system = SystemMessage(
            content=(
                "Bạn là bộ phân loại yêu cầu. Chỉ trả về một nhãn duy nhất từ danh sách: "
                f"{', '.join(self.AGENT_IDS)}. Nếu không phù hợp, trả về 'none'."
            )
        )
        user = HumanMessage(content=text)

        try:
            result: RoutingOutput = await structured_llm.ainvoke([system, user])
            label = result.label.strip().lower()
            return label if label in self.AGENT_IDS else None
        except Exception as e:
            print("[Host] LLM routing failed:", e)
            return None

# Hàm entry-point cho node “host” trong core graph
_host_agent = HostAgent()
async def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return await _host_agent.run(input_data)