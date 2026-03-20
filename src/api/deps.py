from __future__ import annotations
from fastapi import Depends
from functools import lru_cache
from src.agent.agent_manager import AgentManager
from src.memory.memory_manager import MemoryManager
from src.sessions.session_manager import SessionManager

@lru_cache
def get_memory_manager():
    """获取MemoryManager单例，作为FastAPI依赖注入"""
    return MemoryManager()
@lru_cache
def get_agent_manager(memory_manager:MemoryManager = Depends(get_memory_manager)):

    _agent_manager=AgentManager(memory_manager)
    return _agent_manager
@lru_cache
def get_session_manager():
    _session_manager = SessionManager()
    return _session_manager
