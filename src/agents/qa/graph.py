# agent/qa/graph.py
from typing import Dict, Any

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from configs.config_loader import llm_api as model
from agents.jira.graph import graph as jira_agent
from agents.confluence.graph import graph as confluence_agent

from agents.qa.qa import QAAgent

# Load tools create_unit_test & run_unit_test
tools = QAAgent._load_tools()

unit_test_agent = create_react_agent(
    name="unit_test_agent",
    model=model,
    tools=tools,
    prompt="""
You are a Python Unit Testing Expert.

– You must extract exactly 4 arguments from the entire message history:
  `source_file_path`, `test_file_path`, `coverage_xml_path`, and `project_root`.
– If any of them are missing, silently do nothing (return need more information).
– If all are found, call the `create_unit_test` tool and return the result directly.

– You do not explain or reason.
– You do not ask users for clarification.
– You ignore all unrelated messages or context outside of test generation.
"""
)

qa_test_supervisor = create_supervisor(
    agents=[confluence_agent, unit_test_agent],
    model=model,
    # bật ghi lại cặp (AIMessage, ToolMessage) khi supervisor chuyển quyền/agent con thực hiện xong trả về supervisor
    add_handoff_messages=True,
    add_handoff_back_messages=True,
    output_mode="last_message",
    supervisor_name="qa_test_supervisor",
    prompt="""
Bạn là QA Test Supervisor.

## Luồng hành động:
1. Gọi `confluence_agent` để lấy đủ các thông tin kỹ thuật cần thiết từ tài liệu Spaces.
2. Sau khi có đủ thông tin, gọi `unit_test_agent` để:
   – Tạo code test tự động
   – Chạy test và trả kết quả
3. Tổng hợp kết quả rõ ràng, dễ hiểu cho người dùng.

## Quy tắc:
- Trước khi giao nhiệm vụ cho agent con, hãy luôn thực hiện bước suy luận nói ra nhiệm vụ mà Agent phải hoàn thành, sau đó gọi đến agent thay vì trả về END.
– KHÔNG được hỏi lại người dùng.
– KHÔNG được tự suy luận code hay giả định thông tin.
– KHÔNG đọc tài liệu trực tiếp – phải giao nhiệm vụ cho `confluence_agent`.

Giao tiếp với người dùng bằng tiếng Việt. Phản hồi phải ngắn gọn, mạch lạc, đúng trọng tâm.
"""
).compile(name="qa_test_agent")

graph = qa_test_supervisor

# Entry-point cho core_graph
async def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    return await graph.ainvoke(input_data)
