from langgraph.graph import StateGraph, START, END
from agents.Report import report
from typing import Annotated, Any, Dict, TypedDict
from langgraph.graph import Graph
from langgraph.prebuilt import ToolNode
from agents.PM.project_manager import ProjectManagerAgent, TaskInfo

# Define state types
class PMState(TypedDict):
    """State for PM Agent workflow"""
    input: str  # Original user input
    tasks: list[TaskInfo] | None  # Parsed tasks
    current_task: TaskInfo | None  # Current task being processed
    jira_issue: Dict[str, Any] | None  # Created Jira issue
    status: str  # Current status
    answer: str  # Final answer to user

# Initialize PM Agent
pm_agent = ProjectManagerAgent()

# Define nodes
async def parse_tasks(state: PMState) -> PMState:
    """Parse user input into tasks"""
    tasks = await pm_agent._breakdown_into_tasks(state["input"])
    return {**state, "tasks": tasks, "status": "parsed"}

async def create_jira_issue(state: PMState) -> PMState:
    """Create Jira issue for current task"""
    if not state["current_task"]:
        return {**state, "status": "error", "answer": "Không có task để tạo"}
    
    jira_issue = await pm_agent._create_jira_issue(state["current_task"])
    return {**state, "jira_issue": jira_issue, "status": "created"}

async def dispatch_task(state: PMState) -> PMState:
    """Dispatch task to appropriate agent"""
    if not state["current_task"]:
        return {**state, "status": "error", "answer": "Không có task để phân công"}
    
    await pm_agent._dispatch_task(state["current_task"])
    return {**state, "status": "dispatched"}

async def compose_reply(state: PMState) -> PMState:
    """Compose final reply to user"""
    if state["status"] == "error":
        return state
    
    reply = (
        f"Đã xử lý task: {state['current_task']['title']}\n"
        f"Jira issue: {state['jira_issue']['key']}\n"
        "Task đã được phân công cho agent phù hợp."
    )
    return {**state, "answer": reply}

# Define router
def should_continue(state: PMState) -> str:
    """Determine next node based on state"""
    if state["status"] == "error":
        return "compose_reply"
    
    if not state["tasks"]:
        return "compose_reply"
    
    if not state["current_task"]:
        # Get next task
        state["current_task"] = state["tasks"].pop(0)
        return "create_jira_issue"
    
    if state["status"] == "created":
        return "dispatch_task"
    
    if state["status"] == "dispatched":
        if state["tasks"]:
            state["current_task"] = state["tasks"].pop(0)
            return "create_jira_issue"
        return "compose_reply"
    
    return "compose_reply"

# Build graph
def build_pm_graph() -> Graph:
    """Build PM Agent workflow graph"""
    workflow = Graph()
    
    # Add nodes
    workflow.add_node("parse_tasks", parse_tasks)
    workflow.add_node("create_jira_issue", create_jira_issue)
    workflow.add_node("dispatch_task", dispatch_task)
    workflow.add_node("compose_reply", compose_reply)
    
    # Add edges
    workflow.add_edge("parse_tasks", should_continue)
    workflow.add_edge("create_jira_issue", should_continue)
    workflow.add_edge("dispatch_task", should_continue)
    workflow.add_edge("compose_reply", END)
    
    # Set entry point
    workflow.set_entry_point("parse_tasks")
    
    return workflow

# Export graph
pm_graph = build_pm_graph()
