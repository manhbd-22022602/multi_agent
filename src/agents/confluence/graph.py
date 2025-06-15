# agent/pm/graph.py
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from configs.config_loader import llm_api as model
from agents.confluence.confluence import ConfluenceAgent

tools_map = ConfluenceAgent._load_tools()
confluence_read_tools = tools_map["confluence_read"]
confluence_write_tools = tools_map["confluence_write"]

confluence_read_agent = create_react_agent(
    name="confluence_read_agent",
    model=model,
    tools=confluence_read_tools,
    prompt="""
Bạn là chuyên gia đọc dữ liệu confluence. Chỉ thực hiện các thao tác đọc và không sửa đổi dữ liệu. 
"""
)

confluence_write_agent = create_react_agent(
    name="confluence_write_agent",
    model=model,
    tools=confluence_write_tools,
    prompt="""
Bạn là chuyên gia ghi dữ liệu confluence. Chỉ thực hiện các thao tác tạo, cập nhật và xóa issue.
– KHÔNG hỏi lại người dùng. 
– Tự động chọn và gọi tool phù hợp. 
"""
)

# Tạo supervisor cho các sub-agent (confluence write, confluence read)
confluence_agent = create_supervisor(
    supervisor_name="confluence_agent",
    agents=[
        confluence_read_agent,
        confluence_write_agent,
    ],
    model=model,
    prompt="""
Bạn là chuyên gia quản lý confluence.
– KHÔNG hỏi lại người dùng. 
– Tự động chọn và gọi tool phù hợp. 
"""
)

graph = confluence_agent.compile(name="confluence_agent")
    
# Hàm entry-point cho node “host” trong core_graph
async def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return await graph.ainvoke(input_data)

# async def main():
#     messages = await graph.ainvoke({"messages": [{"role": "user", "content": "Project có key 'TP' hiện có bao nhiêu issue?"}]})
#     for m in messages['messages']:
#         m.pretty_print()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())