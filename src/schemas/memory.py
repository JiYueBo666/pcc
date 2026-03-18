from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Literal,List,Optional
from pydantic import BaseModel,Field

#请求模型
class MemoryRequest(BaseModel):
    content: str = Field(..., min_length=1, description="记忆内容，不能为空")
    session_id: str = Field(..., min_length=1, description="会话ID，不能为空")
    role: Literal["user", "system",'assistant'] = Field("user", description="角色，仅支持user/system/assistant")


class MemoryCreateRequest(BaseModel):
    """新增记忆请求模型"""
    content: str = Field(..., min_length=1, description="记忆内容，不能为空")
    session_id: str = Field(..., min_length=1, description="会话ID，不能为空")
    role: Literal["user", "system"] = Field("user", description="角色，仅支持user/system")
class MemoryQueryRequest(BaseModel):
    """查询记忆请求模型（GET请求用Query参数，这里定义参数约束）"""
    session_id:str= Field(..., min_length=1, description="会话ID，不能为空")

class MemoryDeleteRequest(BaseModel):
    """删除记忆请求模型"""
    session_id: str = Field(..., min_length=1, description="会话ID，不能为空")
    delete_all: bool = Field(True, description="是否删除全部")
    content: Optional[str] = Field(None, description="要删除的内容（delete_all=False时必填）")

# ========== 响应模型（Response） ==========
class MemoryItemResponse(BaseModel):
    """单个记忆项响应模型（对齐阶段1的MemoryItem）"""
    content: str
    session_id: str
    role: Literal["user", "system"]
    created_at: datetime

    class Config:
        orm_mode = True  # 支持从dataclass对象转换

class MemoryListResponse(BaseModel):
    """记忆列表响应模型"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: List[MemoryItemResponse] = Field([], description="记忆列表")

class MemoryOperateResponse(BaseModel):
    """记忆操作（增/删）响应模型"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Optional[dict] = Field(None, description="附加数据")