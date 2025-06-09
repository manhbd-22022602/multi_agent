# agent/pm/graph.py
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from configs.config_loader import llm_api as model
from agents.pm.pm import PMAgent

tools_map = PMAgent._load_tools()
jira_read_tools = tools_map["jira_read"]
jira_write_tools = tools_map["jira_write"]
confluence_read_tools = tools_map["confluence_read"]
confluence_write_tools = tools_map["confluence_write"]
github_tools = tools_map["github"]

jira_read_agent = create_react_agent(
    name="jira_read_agent",
    model=model,
    tools=jira_read_tools,
    prompt="""
Bạn là chuyên gia đọc dữ liệu Jira. Chỉ thực hiện các thao tác đọc và không sửa đổi dữ liệu. 
– KHÔNG hỏi lại người dùng. 
– Tự động chọn và gọi tool phù hợp. 
"""
)

jira_write_agent = create_react_agent(
    name="jira_write_agent",
    model=model,
    tools=jira_write_tools,
    prompt="Bạn là chuyên gia ghi dữ liệu Jira. Chỉ thực hiện các thao tác tạo, cập nhật và xóa issue."
)

confluence_read_agent = create_react_agent(
    name="confluence_read_agent",
    model=model,
    tools=confluence_read_tools,
    prompt="Bạn là chuyên gia đọc dữ liệu Confluence. Chỉ thực hiện các thao tác đọc trang và tìm kiếm."
)

confluence_write_agent = create_react_agent(
    name="confluence_write_agent",
    model=model,
    tools=confluence_write_tools,
    prompt="Bạn là chuyên gia ghi dữ liệu Confluence. Chỉ thực hiện các thao tác tạo, cập nhật, xóa trang và thêm bình luận."
)

github_agent = create_react_agent(
    name="github_agent",
    model=model,
    tools=github_tools,
    prompt="Bạn là chuyên gia thao tác GitHub. Chỉ thực hiện các thao tác liên quan đến repository và issue trên GitHub."
)

# fallback agent cho các câu hỏi chung
self_answer_agent = create_react_agent(
    name="self_answer_agent",
    model=model,
    tools=[],
    prompt="Bạn là chuyên gia PM tổng hợp. Trả lời các câu hỏi chung không thuộc phạm vi Jira, Confluence hay GitHub."
)

# Tạo supervisor cho các sub-agent (PM Agent phân cấp)
pm_agent = create_supervisor(
    [
        jira_read_agent,
        jira_write_agent,
        confluence_read_agent,
        confluence_write_agent,
        github_agent,
        self_answer_agent,
    ],
    model=model,
    supervisor_name="pm_supervisor",
    prompt=(
        "Bạn là PM Agent tổng hợp. Khi nhận yêu cầu từ người dùng, hãy phân tích mục tiêu và gọi đúng chuyên gia (Jira đọc, Jira ghi, Confluence đọc, Confluence ghi, GitHub hoặc trả lời chung)."
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