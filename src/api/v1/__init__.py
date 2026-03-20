from __future__ import annotations
from fastapi import APIRouter
from src.api.v1.memory import router as memory_router
from src.api.v1.user import router as user_router
from src.api.v1.agent import router as agent_router

# 聚合v1版本所有路由
router = APIRouter()
router.include_router(memory_router)
router.include_router(user_router)
router.include_router(agent_router)

__all__ = ["router"]