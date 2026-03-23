from __future__ import annotations
from dataclasses import dataclass,field
from typing import Literal,Optional
import time

TaskStatus=Literal['pending','running','completed','failed']

@dataclass
class SubTaskRecord:
    task_id:str
    parent_session_id:str
    child_session_id:str
    agent_id: str
    task: str
    label: Optional[str] = None
    status: TaskStatus = "pending"
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    ended_at: Optional[float] = None