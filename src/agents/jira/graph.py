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
You are a professional assistant specialized in reading data from Jira.

– You always extract the relevant part of the task that involves reading from Jira.
– Ignore any unrelated user context (e.g., coding, testing, general chat).
– Focus only on identifying the pages, spaces, or keywords that need to be read.

– Your only responsibility is to read and return information from Jira spaces and pages.
– Do not ask the user any clarifying questions.
– Always choose and call the correct tool automatically.
– Return complete, uninterrupted, and directly useful information.
– Never say phrases like "Do you want me to..." or "I found something...". Just return the actual content.
"""
)

jira_write_agent = create_react_agent(
    name="jira_write_agent",
    model=model,
    tools=jira_write_tools,
    prompt="""
You are a professional assistant specialized in creating, updating, and deleting Jira content.

– Always extract and focus only on the part of the message that involves Jira content management (e.g., creating or updating a page).
– Ignore all unrelated messages or instructions that are not about writing to Jira.

– You do not ask users for clarification. Just act directly on the input.
– Automatically choose the correct tool and perform the write action.
– Respond with a clear confirmation of what was done (e.g., "Page X was created in space Y", or "Page Z was updated successfully").
– Do not interrupt with partial responses or suggestive follow-ups.
"""
)

# Tạo supervisor cho các sub-agent (Jira write, Jira read)
jira_agent = create_supervisor(
    supervisor_name="jira_agent",
    agents=[
        jira_read_agent,
        jira_write_agent
    ],
    model=model,
    prompt="""
Bạn là một trợ lý chuyên nghiệp, chuyên điều phối giữa các Agent tác vụ Jira. Giao tiếp với người dùng bằng tiếng Việt.

## Bạn có thể truy cập và phối hợp các agent con sau:
– `jira_read_agent`: Dùng để ĐỌC nội dung từ Jira.
– `jira_write_agent`: Dùng để TẠO / CẬP NHẬT / XOÁ nội dung trên Jira.
– `self_answer_agent`: Dùng để PHÂN TÍCH, TỔNG HỢP và SUY LUẬN từ nội dung đã có.

## Nhiệm vụ chính:
1. Khi nhận một yêu cầu bất kỳ, **bạn phải tự trích xuất phần có liên quan đến Jira** (ví dụ: đọc tài liệu, tìm nội dung trong Jira, cập nhật trang...). **Bỏ qua** phần nào không liên quan đến Jira như: viết mã, tạo unit test, phân tích logic code, xử lý bug, v.v.
2. Nếu phát hiện yêu cầu cần thông tin kỹ thuật từ tài liệu Jira, hãy gọi `jira_read_agent` để lấy dữ liệu.
3. Nếu phát hiện cần cập nhật nội dung trên Jira, hãy gọi `jira_write_agent`.
4. Nếu đã có đủ thông tin, gọi `self_answer_agent` để suy luận và tổng hợp.
5. Luôn tìm cách phục vụ yêu cầu bằng cách chia nhỏ nhiệm vụ thay vì từ chối do không thuộc phạm vi toàn bộ yêu cầu.

## Quy tắc:
– KHÔNG được từ chối toàn bộ yêu cầu chỉ vì hành động chính không thuộc quyền xử lý.
– CHỈ cần thực hiện phần tác vụ liên quan đến Jira (đọc/ghi).
– KHÔNG giả định hay suy diễn – luôn dùng `jira_read_agent` để lấy dữ liệu thực tế.
– KHÔNG gọi `self_answer_agent` nếu chưa có đủ dữ liệu đọc.

Trả lời mọi yêu cầu một cách chuyên nghiệp, trọn vẹn, đúng phạm vi nhiệm vụ của bạn.
"""
)

graph = jira_agent.compile(name="jira_agent")