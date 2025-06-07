from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List, TypedDict

from agents.Dev import developer as _dev_agent
from agents.Doc import docu as _doc_agent
from agents.QA import qa as _qa_agent
from configs.settings import LLM
from services.atlassian_mcp import load_atlassian_tools

# LLM selection (reuse helper from host if preferred)
if LLM.startswith("gemini"):
    from langchain_google_genai import ChatGoogleGenerativeAI as _ChatLLM

from langchain.schema import HumanMessage, SystemMessage

# (Optional) – import sub‑agents lazily when needed
from agents.Report import report as _rep_agent

_PM_SYSTEM_PROMPT = (
    "Bạn là **Project‑Manager Agent** trong hệ thống quản lý dự án tự động. "
    "Trách nhiệm của bạn:\n"
    "• Phân tích yêu cầu dự án (tính năng mới, báo lỗi, thay đổi).\n"
    "• Chia nhỏ yêu cầu thành các task kỹ thuật theo template: \n"
    "     {id, title, description, assignee_role, priority, due_date, effort_estimation}.\n"
    "• Quyết định assignee_role trong số [developer, qa, documentation].\n"
    "• Cập nhật trạng thái dự án.\n"
    "• Phân công task cho agent tương ứng và thu thập phản hồi.\n"
    "• Trả về thông báo trạng thái ngắn gọn cho người yêu cầu."
)

# Simple in‑memory "database" for POC; swap with real DB later
_PROJECT_DB: Dict[str, Dict[str, Any]] = {}

class TaskInfo(TypedDict):
    title: str
    description: str
    priority: str
    assignee: str | None
    due_date: str | None
    effort_estimation: str | None

class ProjectManagerAgent:
    """Create/assign tasks & supervise life‑cycle."""

    def __init__(self) -> None:
        self.name = "Project Manager"
        self.llm = _ChatLLM(model=LLM, temperature=0)
        self.tools = None  # Will be initialized in setup()

    async def setup(self) -> None:
        """Initialize MCP tools"""
        tools = await load_atlassian_tools()
        self.tools = tools["atlassian"]

    # ------- Public entry‑point used by Host or graph node -------
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        user_msg: str = input_data.get("text", "")
        user_id: str = input_data.get("user_id", "anonymous")

        # 1. Breakdown user_msg → task list ----------------------------------
        tasks = await self._breakdown_into_tasks(user_msg)
        if not tasks:
            return {
                "status": "failed",
                "answer": "Không thể phân tích yêu cầu thành task cụ thể.",
            }

        # 2. Create Jira issues and update local DB -------------------------
        created_ids: List[str] = []
        for t in tasks:
            # Create Jira issue using MCP tools
            jira_issue = await self._create_jira_issue(t)
            
            # Update local DB
            tid = await self._create_task_record(t, user_id, jira_issue["key"])
            created_ids.append(tid)
            
            # Dispatch to appropriate agent
            await self._dispatch_task(t)

        # 3. Compose PM reply -------------------------------------------------
        reply = (
            f"Đã tạo {len(created_ids)} task mới: {', '.join(created_ids)}. "
            "Anh/chị có muốn điều chỉnh độ ưu tiên hay thời hạn không?"
        )
        return {"status": "success", "answer": reply, "created_tasks": created_ids}

    # ----------------- Internal helpers -----------------
    async def _breakdown_into_tasks(self, message: str) -> List[Dict[str, Any]]:
        prompt = (
            f"{_PM_SYSTEM_PROMPT}\n\n"
            "Phân tích yêu cầu sau thành các task nhỏ. "
            "Trả về mảng JSON.\n\n"
            f"Yêu cầu: >>>{message}<<<"
        )
        raw = await self.llm.ainvoke(prompt)
        import json as _json
        try:
            tasks = _json.loads(raw.content)
            assert isinstance(tasks, list)
            return tasks  # type: ignore[return‑value]
        except Exception:
            return []

    async def _create_jira_issue(self, task: TaskInfo) -> Dict[str, Any]:
        """Create Jira issue using MCP tools"""
        if not self.tools:
            await self.setup()
        
        # Find create_issue tool
        create_issue_tool = next(t for t in self.tools if t.name == "create_issue")
        
        # Prepare issue data
        issue_data = {
            "fields": {
                "summary": task["title"],
                "description": task["description"],
                "priority": {"name": task["priority"]},
            }
        }
        if task.get("assignee"):
            issue_data["fields"]["assignee"] = {"name": task["assignee"]}
        if task.get("due_date"):
            issue_data["fields"]["duedate"] = task["due_date"]
        
        # Create issue
        result = await create_issue_tool.ainvoke(issue_data)
        return result

    async def _create_task_record(self, task: Dict[str, Any], created_by: str, jira_key: str) -> str:
        tid = f"TASK‑{len(_PROJECT_DB) + 1:04d}"
        _PROJECT_DB[tid] = {
            **task,
            "id": tid,
            "jira_key": jira_key,
            "created_by": created_by,
            "created_at": _dt.datetime.utcnow().isoformat(),
            "status": "open",
        }
        return tid

    async def _dispatch_task(self, task: Dict[str, Any]) -> None:
        role = task.get("assignee_role")
        if role == "developer":
            await _dev_agent.run({"task": task})  # type: ignore[attr‑defined]
        elif role == "qa":
            await _qa_agent.run({"task": task})  # type: ignore[attr‑defined]
        elif role == "documentation":
            await _doc_agent.run({"task": task})  # type: ignore[attr‑defined]

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current status of a task including Jira updates"""
        if task_id not in _PROJECT_DB:
            return {"status": "not_found"}
        
        task = _PROJECT_DB[task_id]
        
        # Get Jira status using MCP tools
        if not self.tools:
            await self.setup()
        
        get_issue_tool = next(t for t in self.tools if t.name == "get_issue")
        jira_status = await get_issue_tool.ainvoke({"issue_key": task["jira_key"]})
        
        return {
            "status": "success",
            "task": {**task, "jira_status": jira_status}
        }

# LangGraph export ------------------------------------------------------------
pm_agent = ProjectManagerAgent()
async def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return await pm_agent.run(input_data)
