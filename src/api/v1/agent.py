from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, Query, HTTPException, Body, Response
from fastapi.responses import StreamingResponse
from src.api.deps import get_agent_manager
from src.api.deps import get_memory_manager
from src.api.deps import get_session_manager
from src.agent.agent_manager import AgentManager
from src.memory.memory_manager import MemoryManager
from src.sessions.session_manager import SessionManager
from src.schemas.agent import ChatResponse, ChatStreamResponse
import json
import uuid

# 创建路由实例（v1版本）
router = APIRouter(prefix="/v1/agent", tags=["agent"])

@router.post('/chat', summary="Chat with agent")
async def chat(
    message: str = Body(..., embed=False, description="用户消息内容"),
    agent_id: str = Body("main", description="Agent ID"),
    stream: bool = Body(False, description="是否使用流式响应"),
    agent_manager: AgentManager = Depends(get_agent_manager),
    session_manager: SessionManager = Depends(get_session_manager),
    raw_session_id: Optional[str] = Cookie(None, alias="chat_session_id"),
    response:Response=None
):
    """
    与Agent进行对话

    参数:
        message: 用户消息内容
        agent_id: Agent ID，默认为main
        stream: 是否使用流式响应，默认为False

    返回:
        如果stream为True，返回流式响应；否则返回完整响应
    """
    message = message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")

    #cookie获取session id
    session_id=await session_manager.get_session_id(session_id=raw_session_id,response=response)

    # 如果请求流式响应
    if stream:
        headers={
            'Set-Cookie':response.headers['set-cookie']
        } if response.headers.get('set-cookie') else {}
        async def generate():
            """生成流式响应"""
            async for chunk in agent_manager.astream(
                message=message,
                session_id=session_id,
                agent_id=agent_id
            ):
                # 将每个chunk转换为JSON格式并添加换行符
                yield json.dumps(chunk, ensure_ascii=False) + "\n"

        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers=headers
        )

    # 非流式响应
    else:
        full_response = ""
        async for chunk in agent_manager.astream(
            message=message,
            session_id=session_id,
            agent_id=agent_id
        ):
            if chunk.get("type") == "token":
                full_response += chunk.get("content", "")
            elif chunk.get("type") == "error":
                raise HTTPException(status_code=500, detail=chunk.get("error"))

        return ChatResponse(
            code=200,
            message="success",
            data={
                "response": full_response,
                "session_id": session_id,
                "agent_id": agent_id
            }
        )