from __future__ import annotations
from src.memory_manager import MemoryManager
from src.userInfo import UserSessionManager
from src.agent.agent_manager import AgentManager

# 单例模式：保证整个API服务中只有一个MemoryManager实例
_memory_manager: MemoryManager | None = None
_user_manager:UserSessionManager|None=None
_agent_manager:AgentManager|None=None

def get_memory_manager() -> MemoryManager:
    """获取MemoryManager单例，作为FastAPI依赖注入"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager

def get_user_manager():
    global _user_manager
    if _user_manager is None:
        _user_manager = UserSessionManager()
    return _user_manager

def get_agent_manager():
    global _agent_manager
    if _agent_manager is None:
        _agent_manager = AgentManager()
    return _agent_manager