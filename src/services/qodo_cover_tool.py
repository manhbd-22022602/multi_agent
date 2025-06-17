import subprocess
import requests
import os
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from configs.config_loader import QODO_URL

class CreateUnitTestArgs(BaseModel):
    source_file_path: str = Field(..., title="Source File Path", description="Path to the source file to test.")
    test_file_path: str = Field(..., title="Test File Path", description="Path where generated tests should be saved.")
    coverage_xml_path: str = Field(..., title="Coverage XML Path", description="Path to coverage XML file.")
    project_root: str = Field(..., title="Project Root", description="Root path of the project.")

@tool(
    name_or_callable="create_unit_test",
    description=(
        "Calls Qodo Cover to generate unit tests for a given Python source file using test coverage analysis.\n\n"
        "Args:\n"
        "    source_file_path (str): Path to the file needing test.\n"
        "Returns:\n"
        "    str: JSON or YAML-formatted result of test generation, or error message if failed."
    ),
    # args_schema=CreateUnitTestArgs.model_json_schema()
)
def create_unit_test(source_file_path: str) -> str:
    """
    Gọi Qodo Cover để tạo unit test tự động cho một file mã nguồn cụ thể.
    """
    project_root = os.path.dirname(source_file_path)
    filename = os.path.basename(source_file_path)
    
    test_file_path = os.path.join(project_root, f"test_{filename}")
    coverage_xml_path = os.path.join(project_root, "coverage.xml")

    payload = {
        "source_file_path": source_file_path,
        "test_file_path": test_file_path,
        "project_root": project_root,
        "coverage_report_path": coverage_xml_path,
        "test_command": "pytest --cov=. --cov-report=xml --cov-report=term",
        "test_command_dir": project_root,
        "coverage_type": "cobertura",
        "desired_coverage": 90,
        "max_iterations": 3
    }

    try:
        response = requests.post(f"{QODO_URL}/run-cover", json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("stdout", "")
    except Exception as e:
        return f"[ERROR create_unit_test] {e}"

class RunUnitTestArgs(BaseModel):
    test_command_dir: str = Field(..., title="Test Command Directory", description="Directory in which to run the test command.")
    test_command: str = Field(..., title="Test Command", description="The test command to execute (e.g., pytest ...).")

@tool(
    name_or_callable="run_unit_test",
    description=(
        "Runs a given test command (e.g., pytest) inside a specified directory.\n\n"
        "Args:\n"
        "    test_command_dir (str): Path to the directory where tests should be run.\n"
        "    test_command (str): Shell command to execute tests.\n\n"
        "Returns:\n"
        "    str: Test execution output (stdout + stderr)."
    ),
    args_schema=RunUnitTestArgs.model_json_schema()
)
def run_unit_test(test_command_dir: str, test_command: str) -> str:
    """
    Thực thi một câu lệnh test (như pytest) trong thư mục chỉ định.
    """
    import subprocess

    try:
        result = subprocess.run(
            test_command,
            cwd=test_command_dir,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return result.stdout
    except Exception as e:
        return f"[ERROR run_unit_test] {e}"

class CallApiEndpointArgs(BaseModel):
    method: str = Field(..., title="HTTP Method", description="HTTP method to use (GET, POST, etc.).")
    url: str = Field(..., title="URL", description="Full URL of the API endpoint.")
    headers: dict = Field(default_factory=dict, title="Headers", description="HTTP headers to include.")
    params: dict = Field(default_factory=dict, title="Query Parameters", description="Query parameters for the request.")
    data: dict = Field(default_factory=dict, title="Form Data", description="Form data (for POST/PUT).")
    json_body: dict = Field(default_factory=dict, title="JSON Body", description="JSON body (for POST/PUT).")

@tool(
    name_or_callable="call_api_endpoint",
    description=(
        "Calls any HTTP API endpoint using the specified method, URL, headers, and body.\n\n"
        "Args:\n"
        "    method (str): HTTP method like GET, POST, PUT, DELETE.\n"
        "    url (str): Full API URL.\n"
        "    headers (dict): Request headers.\n"
        "    params (dict): Query parameters.\n"
        "    data (dict): Form data for non-JSON body.\n"
        "    json_body (dict): JSON body for the request.\n\n"
        "Returns:\n"
        "    str: Status code and response body of the API call."
    ),
    args_schema=CallApiEndpointArgs.model_json_schema()
)
def call_api_endpoint(method: str, url: str, headers: dict = None, params: dict = None, data: dict = None, json_body: dict = None) -> str:
    """
    Gọi một API bất kỳ qua HTTP với các thiết lập cụ thể như method, headers, payload.
    """
    import requests

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json_body,
            timeout=30
        )
        return f"[{response.status_code}] {response.text}"
    except Exception as e:
        return f"[ERROR call_api_endpoint] {e}"