# graph/core_graph.py
from typing import TypedDict, Literal, List, Optional, Any, Dict
from langgraph.graph import StateGraph, START, END
from agents.dev import developer
from agents.docu import docu
from agents.host import graph as host
from agents.pm import graph as pm
from agents.qa import qa
from agents.report import report

class Message(TypedDict):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    # Với message do tool trả về, có thể đặt tên tool vào trường name
    name: Optional[str]

# Khai báo State
class ChatState(TypedDict, total=False):
    # Loại sự kiện: chat từ user hoặc tool trả về kết quả
    event: Literal["chat", "tool"]
    # Lịch sử message (system/user/assistant/tool)
    messages: List[Message]
    # Khi user force chọn agent (dev/qa/pm/...)
    forced: Optional[str]
    # Agent tiếp theo do Host hoặc Supervisor decide
    next: Optional[str]
    # Câu trả lời cuối cùng sẽ trả về cho user
    answer: Optional[str]
    # Thông tin về tool đang gọi (nếu event là "tool")
    tool: Optional[str]
    # Tham số truyền vào tool
    tool_input: Optional[Any]
    # Kết quả trả về từ tool
    tool_output: Optional[Any]
    # Metadata tuỳ ý cho mở rộng (tracking, debug, ...)
    metadata: Optional[Dict[str, Any]]
    # TODO: Xoá text ở core và Host Agent, thay thế bằng messages
    # Prompt của user
    text: str

# Build graph
def build_core_graph():
    g = StateGraph(ChatState)

    # Node IDs phải trùng khoá trong ChatState["next"]
    g.add_node("host",   host.run)
    g.add_node("pm",     pm.run)
    # g.add_node("dev",    developer.run)
    # g.add_node("qa",     qa.run)
    # g.add_node("docu",   docu.run)
    # g.add_node("report", report.run)

    # Edges
    g.add_edge(START, "host")        # luôn bắt đầu ở Host

    # Host có thể rẽ sang 5 agent kia hoặc kết thúc
    g.add_conditional_edges(
        "host",
        lambda s: s.get("next", "end"),
        {
            "pm": "pm",
            # "dev": "dev",
            # "qa": "qa",
            # "docu": "docu",
            # "report": "report",
            "end": END,      # Host tự chốt câu trả lời
        },
    )

    # for leaf in ["pm", "dev", "qa", "docu", "report"]:
        # g.add_edge(leaf, END)

    return g.compile()

GRAPH = build_core_graph()

# Router gọi graph bên phía Streamlit (app/main.py) 
# Ở layer cao nhất (trong test hoặc trong Streamlit) nhớ dùng asyncio.run(...) hay await graph_router(...).
async def graph_router(text: str, target_agent: str | None):
    """
    - target_agent None  -> Auto (Host tự quyết).
    - target_agent "dev" -> ép Host route sang Dev, ...
    """
    state: ChatState = {
        "event": "chat",
        "text":  text,
        "forced": target_agent,   # truyền xuống để Host (Auto mode)/Target xử lý
        "messages": [{"role": "user", "content": text}],
    }
    out = await GRAPH.ainvoke(state)
    return out

# export graph để LangGraph CLI detect
graph = GRAPH