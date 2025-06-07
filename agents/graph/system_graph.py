from langgraph.graph import StateGraph, START, END
from agents.Dev import developer
from agents.Doc import docu
from agents.Host import host
from agents.PM import project_manager
from agents.QA import qa
from agents.Report import report

def build_core_graph():
    g = StateGraph()

    # Nodes
    g.add_node("host_agent",      host.run)
    g.add_node("pm_agent",        project_manager.run)
    # g.add_node("dev_agent",       developer.run)
    # g.add_node("qa_agent",        qa.run)
    # g.add_node("docu_agent",      docu.run)
    # g.add_node("report_agent",    report.run)

    # Simple deterministic edges — PM quyết định
    g.add_edge(START,  "host_agent")
    g.add_edge("host_agent", END)  # fallback

    return g.compile()

GRAPH = build_core_graph()

def graph_router(text: str, target_agent: str | None):
    """If target_agent is None → auto mode → host decides."""
    state = {"event": "chat", "text": text, "forced": target_agent}
    out  = GRAPH.invoke(state)
    return out["answer"]
