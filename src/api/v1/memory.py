from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from src.memory_manager import MemoryManager, MemoryItem
from src.userInfo import UserSessionManager
from src.schemas.memory import (
    MemoryCreateRequest,
    MemoryQueryRequest,
    MemoryDeleteRequest,
    MemoryItemResponse,
    MemoryListResponse,
    MemoryOperateResponse
)
from src.api.deps import get_memory_manager,get_user_manager

# 创建路由实例（v1版本）
router = APIRouter(prefix="/v1/memory", tags=["memory"])

# ========== 新增记忆接口 ==========
@router.post("/", response_model=MemoryOperateResponse, summary="新增记忆")
def create_memory(
    req: MemoryCreateRequest = Body(...),
    username:str=Body(None,description='绑定用户名'),
    mm: MemoryManager = Depends(get_memory_manager),
    usm: UserSessionManager = Depends(get_user_manager),
):
    try:
        # 调用阶段1的核心逻辑
        memory = mm.add_memory(
            content=req.content,
            session_id=req.session_id,
            role=req.role,
        )

        if username and username.strip():
            usm.bind_session_to_user(username,req.session_id)
        return MemoryOperateResponse(
            code=200,
            message="记忆新增成功",
            data={"memory_id": f"{memory.session_id}_{memory.created_at.timestamp()}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误：{str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")

# ========== 查询记忆接口 ==========
@router.get("/", response_model=MemoryListResponse, summary="查询会话记忆")
def list_memories(
    session_id: str = Query(..., min_length=1, description="会话ID"),
    mm: MemoryManager = Depends(get_memory_manager)
):
    try:
        # 调用阶段1的核心逻辑（生成器转列表）
        memories: List[MemoryItem] = list(mm.get_memories(session_id=session_id))
        # 转换为响应模型
        memory_responses = [
            MemoryItemResponse(
                content=mem.content,
                session_id=mem.session_id,
                role=mem.role,
                created_at=mem.created_at
            )
            for mem in memories
        ]
        return MemoryListResponse(
            code=200,
            message=f"查询到{len(memory_responses)}条记忆",
            data=memory_responses
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")

# ========== 删除记忆接口 ==========
@router.delete("/", response_model=MemoryOperateResponse, summary="删除记忆")
def delete_memories(
    req: MemoryDeleteRequest = Body(...),
    mm: MemoryManager = Depends(get_memory_manager)
):
    try:
        # 参数校验（delete_all=False时content不能为空）
        if not req.delete_all and req.content is None:
            raise HTTPException(status_code=400, detail="delete_all=False时，content不能为空")
        
        # 调用阶段1的核心逻辑
        success = mm.delete_memories(
            session_id=req.session_id,
            delete_all=req.delete_all,
            content=req.content
        )
        
        if success:
            msg = "删除全部记忆成功" if req.delete_all else f"删除包含'{req.content}'的记忆成功"
            return MemoryOperateResponse(code=200, message=msg)
        else:
            raise HTTPException(status_code=500, detail="删除记忆失败")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"参数错误：{str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"服务器错误：{str(e)}")