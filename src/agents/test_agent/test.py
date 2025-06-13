# agent/pm/graph.py
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_core.tools import tool

from configs.config_loader import llm_api as model

@tool
def test_write(str):
    """Ghi dữ liệu vào hệ thống."""
    return f"Write {str} successfully!"

@tool
def test_read(str):
    """Đọc dữ liệu từ hệ thống."""
    return f"Read {str} successfully!"

@tool
def hello_world(str):
    """Trả lời chào hỏi đơn giản."""
    return f"Hello {str}!"

jira_read_agent = create_react_agent(
    name="jira_read_agent",
    model=model,
    tools=[test_read],
    prompt="""
Bạn là chuyên gia đọc dữ liệu Jira. Chỉ thực hiện các thao tác đọc và không sửa đổi dữ liệu. 
– KHÔNG hỏi lại người dùng. 
– Tự động chọn và gọi tool phù hợp. 
"""
)

jira_write_agent = create_react_agent(
    name="jira_write_agent",
    model=model,
    tools=[test_write],
    prompt="Bạn là chuyên gia ghi dữ liệu Jira. Chỉ thực hiện các thao tác tạo, cập nhật và xóa issue."
)

confluence_read_agent = create_react_agent(
    name="confluence_read_agent",
    model=model,
    tools=[test_read],
    prompt="Bạn là chuyên gia đọc dữ liệu Confluence. Chỉ thực hiện các thao tác đọc trang và tìm kiếm."
)

confluence_write_agent = create_react_agent(
    name="confluence_write_agent",
    model=model,
    tools=[test_write],
    prompt="Bạn là chuyên gia ghi dữ liệu Confluence. Chỉ thực hiện các thao tác tạo, cập nhật, xóa trang và thêm bình luận."
)

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
).compile(name="jira_agent")

confluence_agent = create_supervisor(
    supervisor_name="confluence_agent",
    agents=[
        confluence_read_agent,
        confluence_write_agent,
    ],
    model=model,
    prompt="Bạn là chuyên gia Confluence."
).compile(name="confluence_agent")

# fallback agent cho các câu hỏi chung
self_answer_agent = create_react_agent(
    name="self_answer_agent",
    model=model,
    tools=[hello_world],
    prompt="Bạn là chuyên gia PM tổng hợp. Trả lời các câu hỏi chung không thuộc phạm vi Jira, Confluence hay GitHub."
)

# Tạo supervisor cho các sub-agent (PM Agent phân cấp)
pm_agent = create_supervisor(
    supervisor_name="pm_supervisor",
    agents= [
        jira_agent,
        confluence_agent,
        self_answer_agent,
    ],
    model=model,
    prompt=(
        "Bạn là PM Agent tổng hợp. Khi nhận yêu cầu từ người dùng, hãy phân tích mục tiêu và gọi đúng Agent (Jira, Confluence, hoặc trả lời chung)."
        " Sau khi có kết quả từ sub-agent, tổng hợp và trả lời ngắn gọn rõ ràng bằng tiếng Việt."
        "Phải đảm bảo có đủ thông tin để trả lời câu hỏi của người dùng, không được yêu cầu người dùng cung cấp thêm thông tin."
    )
)
graph = pm_agent.compile(name="pm_graph")