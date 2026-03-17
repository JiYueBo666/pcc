from __future__ import annotations
from src.memory_manager import MemoryManager

# 单例模式：保证整个API服务中只有一个MemoryManager实例
_memory_manager: MemoryManager | None = None

def get_memory_manager() -> MemoryManager:
    """获取MemoryManager单例，作为FastAPI依赖注入"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager