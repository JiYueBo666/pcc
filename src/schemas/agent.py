from __future__ import annotations
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ========== 请求模型 ==========

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, description="用户消息内容")
    session_id: Optional[str] = Field(None, description="会话ID，不提供时自动创建")
    agent_id: str = Field("main", description="Agent ID，默认为main")
    stream: bool = Field(False, description="是否使用流式响应")

# ========== 响应模型 ==========

class ChatResponse(BaseModel):
    """聊天响应模型"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="提示信息")
    data: Dict[str, Any] = Field(..., description="响应数据")

class ChatStreamResponse(BaseModel):
    """流式聊天响应模型"""
    type: Literal["token", "tool_start", "tool_end", "error"] = Field(..., description="响应类型")
    content: Optional[str] = Field(None, description="内容片段")
    tool_name: Optional[str] = Field(None, description="工具名称")
    tool_input: Optional[Dict[str, Any]] = Field(None, description="工具输入")
    tool_output: Optional[str] = Field(None, description="工具输出")
    error: Optional[str] = Field(None, description="错误信息")
