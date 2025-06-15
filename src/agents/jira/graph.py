# agent/pm/graph.py
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from configs.config_loader import llm_api as model
from agents.jira.jira import JiraAgent

tools_map = JiraAgent._load_tools()
jira_read_tools = tools_map["jira_read"]
jira_write_tools = tools_map["jira_write"]

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

# Tạo supervisor cho các sub-agent (Jira write, Jira read)
jira_agent = create_supervisor(
    supervisor_name="jira_agent",
    agents=[
        jira_read_agent,
        jira_write_agent,
    ],
    model=model,
    prompt="""
Bạn là chuyên gia quản lý Jira.
– KHÔNG hỏi lại người dùng. 
– Tự động chọn và gọi tool phù hợp. 
"""
)

graph = jira_agent.compile(name="jira_agent")