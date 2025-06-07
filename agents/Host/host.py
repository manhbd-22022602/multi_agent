from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from configs.settings import LLM

# Dynamically select the proper LangChain chat wrapper
if LLM.startswith("gemini"):
    from langchain_google_genai import ChatGoogleGenerativeAI as _ChatLLM

from langchain.schema import HumanMessage, SystemMessage

# **Avoid circular imports** – import inside function
# (ProjectManagerAgent lives in agents.project_manager)

_SYSTEM_PROMPT = (
    "Bạn là **Host Agent**, một trợ lý AI cho nhân viên trong công ty phần mềm. "
    "Mục tiêu của bạn:\n"
    "1. Trả lời nhanh chóng và chính xác các câu hỏi về công ty hoặc dự án.\n"
    "2. Phát hiện khi yêu cầu liên quan đến quản lý dự án (tạo task, phân công, trạng thái) và chuyển đến Project‑Manager Agent.\n"
    "3. Nhớ vai trò của nhân viên (Dev/QA/PM/…); điều chỉnh giọng điệu và độ chi tiết phù hợp.\n"
    "4. Luôn trả lời bằng cùng ngôn ngữ mà nhân viên sử dụng.\n"
    "5. Chuyển các yêu cầu kỹ thuật đến Developer Agent.\n"
    "6. Chuyển các yêu cầu kiểm thử đến QA Agent."
)

_ROLE_INTENT_CLASSIFIER = (
    "Bạn là một bộ phân loại. Đọc tin nhắn của nhân viên được đánh dấu bởi >>> và trả về JSON với:\n"
    "  • role   – vai trò có thể của người nói (pm, dev, qa, other)\n"
    "  • intent – một trong [project_management, technical_development, testing, general_qa] dựa trên nội dung tin nhắn.\n"
    "Chỉ trả về JSON.\n>>>\n{message}\n>>>"
)

class HostAgent:
    """Central concierge + router.

    Expected **input_data** structure:
    ```python
    {
        "user_id": str,          # employee identifier
        "text": str,            # message from employee
        "forced": Optional[str] # optional hard route key ("pm", "dev", "qa", "self")
    }
    ```
    Returns a **dict** containing at minimum `answer` and `routed` keys.
    """

    def __init__(self) -> None:
        self.name = "Host"
        self.llm = _ChatLLM(model=LLM, temperature=0.2)
        # Lazy‑instantiate agents to avoid circular imports
        self._pm: Optional["ProjectManagerAgent"] = None
        self._dev: Optional["DeveloperAgent"] = None
        self._qa: Optional["QAAgent"] = None

    # ------------- Public API -------------
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text: str = input_data.get("text", "")
        forced: Optional[str] = input_data.get("forced")

        # 1. Forced routing? ---------------------------------------------------
        if forced == "pm":
            return await self._route_to_pm(input_data)
        if forced == "dev":
            return await self._route_to_dev(input_data)
        if forced == "qa":
            return await self._route_to_qa(input_data)
        if forced == "self":
            return await self._answer_general(text)

        # 2. Classify role & intent -------------------------------------------
        role_intent_json = await self._classify_intent(text)
        intent = role_intent_json.get("intent", "general_qa")

        # 3. Route or answer ---------------------------------------------------
        if intent == "project_management":
            return await self._route_to_pm(input_data)
        elif intent == "technical_development":
            return await self._route_to_dev(input_data)
        elif intent == "testing":
            return await self._route_to_qa(input_data)
        else:
            return await self._answer_general(text)

    # ------------- Internal helpers -------------
    async def _classify_intent(self, message: str) -> Dict[str, str]:
        prompt = _ROLE_INTENT_CLASSIFIER.format(message=message)
        raw = await self.llm.ainvoke(prompt)
        # Guard – make sure we always return a dict
        try:
            import json as _json
            parsed = _json.loads(raw.content.strip())
            if isinstance(parsed, dict):
                return parsed
        except Exception:  # pragma: no cover – best‑effort fallback
            return {"role": "other", "intent": "general_qa"}
        return parsed  # type: ignore[misc]

    async def _answer_general(self, message: str) -> Dict[str, Any]:
        response = await self.llm.ainvoke([
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=message),
        ])
        return {
            "status": "success",
            "answer": response.content,
            "routed": "self",
        }

    async def _route_to_pm(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if self._pm is None:
            from agents.PM.project_manager import ProjectManagerAgent  # pylint: disable=import‑outside‑top‑level
            self._pm = ProjectManagerAgent()
        result = await self._pm.run(input_data)
        result["routed"] = "pm"
        return result

    async def _route_to_dev(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if self._dev is None:
            from agents.Dev.developer import DeveloperAgent  # pylint: disable=import‑outside‑top‑level
            self._dev = DeveloperAgent()
        result = await self._dev.run(input_data)
        result["routed"] = "dev"
        return result

    async def _route_to_qa(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if self._qa is None:
            from agents.QA.qa import QAAgent  # pylint: disable=import‑outside‑top‑level
            self._qa = QAAgent()
        result = await self._qa.run(input_data)
        result["routed"] = "qa"
        return result

# The function exported for LangGraph node wiring
host_agent = HostAgent()
async def run(input_data: Dict[str, Any]) -> Dict[str, Any]:  # noqa: D401 – simple wrapper
    """Entry‑point used by LangGraph builder."""
    return await host_agent.run(input_data)
