# src/runtime/session_runtime.py
from dataclasses import dataclass, field
from collections import deque
from typing import Any, Deque, Optional
import asyncio

@dataclass
class QueueRequest:
    request_id: str
    message: str
    agent_id: str
    session_id: str
    stream: bool = False
    event_queue:Optional[asyncio.Queue] = None

@dataclass
class SessionRuntime:
    session_id: str
    is_busy: bool = False
    active_task: Optional[Any] = None
    drain_task: Optional[Any] = None
    pending_requests: Deque[QueueRequest] = field(default_factory=deque)
    partial_output: str = ""
    user_aborted: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
