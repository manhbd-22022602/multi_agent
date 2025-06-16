# agent/qa/qa.py
from __future__ import annotations
import logging
from langchain.tools import StructuredTool
from services.qodo_cover_tool import create_unit_test, run_unit_test, call_api_endpoint

logger = logging.getLogger(__name__)
tools_cache: list[StructuredTool] = {}

class QAAgent:
    def __init__(self) -> None:
        pass
    
    @staticmethod
    def _load_tools() -> dict[str, list[StructuredTool]]:
        global tools_cache
        if tools_cache:
            return tools_cache

        tools_cache = [
            create_unit_test,
            run_unit_test,
            call_api_endpoint
        ]

        return tools_cache