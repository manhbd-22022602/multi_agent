# agent/pm/graph.py
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from configs.config_loader import llm_api
from agents.jira.graph import graph as jira_agent
from agents.confluence.graph import graph as confluence_agent

# from agents.pm.pm import PMAgent

# tools_map = PMAgent._load_tools()
# github_tools = tools_map["github"]

# fallback agent cho các câu hỏi chung
self_answer_agent = create_react_agent(
    name="self_answer_agent",
    model=llm_api,
    tools=[],
    prompt="Bạn là chuyên gia PM tổng hợp. Trả lời các câu hỏi chung không thuộc phạm vi Jira, Confluence hay GitHub."
)

# Tạo supervisor cho các sub-agent (PM Agent phân cấp)
pm_agent = create_supervisor(
    # bật ghi lại cặp (AIMessage, ToolMessage) khi supervisor chuyển quyền/agent con thực hiện xong trả về supervisor
    add_handoff_messages=True,
    add_handoff_back_messages=True,
    output_mode="last_message",
    agents=[
        jira_agent,
        confluence_agent,
        self_answer_agent,
    ],
    model=llm_api,
    supervisor_name="pm_supervisor",
    prompt=(
        "Bạn là PM Agent tổng hợp. Khi nhận yêu cầu từ người dùng, hãy phân tích mục tiêu và gọi đúng chuyên gia (Jira, Confluence hoặc trả lời chung)."
        " Sau khi có kết quả từ sub-agent, tổng hợp và trả lời ngắn gọn rõ ràng bằng tiếng Việt."
        "Phải đảm bảo có đủ thông tin để trả lời câu hỏi của người dùng, không được yêu cầu người dùng cung cấp thêm thông tin."
    )
).compile(name="pm_agent")

graph = pm_agent
    
# Hàm entry-point cho node “host” trong core_graph
async def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return await graph.ainvoke(input_data)

# async def main():
#     messages = await pm_agent.ainvoke({"messages": [{"role": "user", "content": "Project có key 'TP' hiện có bao nhiêu issue?"}]})
#     for m in messages['messages']:
#         m.pretty_print()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())