# graph/core_graph.py
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, START, END
from agents.Dev import developer
from agents.Doc import docu
from agents.Host import host
from agents.PM import project_manager
from agents.QA import qa
from agents.Report import report

# Khai báo State
class ChatState(TypedDict, total=False):
    event:   Literal["chat"]
    text:    str            # user prompt
    forced:  Optional[str]  # "dev", "qa", ...
    next:    Optional[str]  # host chọn route
    answer:  Optional[str]  # câu trả lời cuối

# Build graph
def build_core_graph():
    g = StateGraph(ChatState)

    # Node IDs phải trùng khoá trong ChatState["next"]
    g.add_node("host",   host.run)
    g.add_node("pm",     project_manager.run)
    g.add_node("dev",    developer.run)
    g.add_node("qa",     qa.run)
    g.add_node("docu",   docu.run)
    g.add_node("report", report.run)

    # Edges
    g.add_edge(START, "host")        # luôn bắt đầu ở Host

    # Host có thể rẽ sang 5 agent kia hoặc kết thúc
    g.add_conditional_edges(
        "host",
        lambda s: s.get("next", "end"),
        {
            "pm": "pm",
            "dev": "dev",
            "qa": "qa",
            "docu": "docu",
            "report": "report",
            "end": END,      # Host tự chốt câu trả lời
        },
    )

    for leaf in ["pm", "dev", "qa", "docu", "report"]:
        g.add_edge(leaf, END)

    return g.compile()

GRAPH = build_core_graph()

# Router gọi graph bên phía Streamlit (app/main.py)
def graph_router(text: str, target_agent: str | None):
    """
    - target_agent None  -> Auto (Host tự quyết).
    - target_agent "dev" -> ép Host route sang Dev, ...
    """
    state: ChatState = {
        "event": "chat",
        "text":  text,
        "forced": target_agent,   # truyền xuống để Host (Auto mode)/Target xử lý
    }
    out = GRAPH.invoke(state)
    return out["answer"]
