# graph/core_graph.py
from typing import TypedDict, Literal, List, Optional, Any, Dict
from langgraph.graph import StateGraph, START, END
from agents.host import graph as host
from agents.pm import graph as pm
from agents.qa import graph as qa

from agents.host.state import ChatState
# Build graph
def build_core_graph():
    g = StateGraph(ChatState)

    # Node IDs phải trùng khoá trong ChatState["next"]
    g.add_node("host",   host.run)
    g.add_node("pm",     pm.run)
    # g.add_node("dev",    developer.run)
    g.add_node("qa",     qa.run)

    # Edges
    g.add_edge(START, "host")        # luôn bắt đầu ở Host

    # Host có thể rẽ sang 5 agent kia hoặc kết thúc
    g.add_conditional_edges(
        "host",
        lambda s: s.get("next", "end"),
        {
            "pm": "pm",
            "qa": "qa",
            "end": END,      # Host tự chốt câu trả lời
        },
    )

    for leaf in ["pm", "qa",]:
        g.add_edge(leaf, END)

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