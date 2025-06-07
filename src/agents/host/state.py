# agent/host/state.py
from typing import TypedDict, Literal, Optional

class HostState(TypedDict, total=False):
    event: Literal["chat"]
    text: str
    forced: Optional[str]
    next: Optional[str]
    answer: Optional[str]