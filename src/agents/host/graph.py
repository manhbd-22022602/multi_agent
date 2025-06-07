# agent/host/graph.py
from typing import Dict, Any
from agents.host.state import HostState
from agents.host.host import HostAgent
from langgraph.graph import StateGraph, START, END

def build_graph() -> StateGraph:
    host_agent = HostAgent()
    sg = StateGraph(HostState)

    sg.add_node("rule_based", host_agent.rule_based)
    sg.add_node("llm_select", host_agent.llm_select)
    sg.add_node("finalize", host_agent.finalize)

    sg.add_edge(START, "rule_based")

    # RULE-BASED: nếu đã có next  ⟹ END, ngược lại ⟹ llm_select
    sg.add_conditional_edges(
        "rule_based",
        lambda s: "exit" if host_agent.forced_is_valid(s.get("forced")) else "cont",
        {"exit": END, "cont": "llm_select"},
    )

    # LLM-SELECT: nếu đã có next ⟹ END, ngược lại ⟹ finalize
    sg.add_conditional_edges(
        "llm_select",
        lambda s: "exit" if "next" in s else "cont",
        {"exit": END, "cont": "finalize"},
    )
    
    sg.add_edge("finalize", END)
    return sg.compile()

graph = build_graph()

# Hàm entry-point cho node “host” trong core_graph
async def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return await graph.ainvoke(input_data)


