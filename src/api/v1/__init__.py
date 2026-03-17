from __future__ import annotations
from fastapi import APIRouter
from src.api.v1.memory import router as memory_router

# 聚合v1版本所有路由
router = APIRouter()
router.include_router(memory_router)

__all__ = ["router"]