from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends,HTTPException, Body, Response
from fastapi.responses import StreamingResponse
from src.api.deps import get_agent_manager
from src.api.deps import get_session_manager
from src.agent.agent_manager import AgentManager
from src.memory.memory_manager import MemoryManager
from src.sessions.session_manager import SessionManager
from src.schemas.agent import ChatResponse, ChatStreamResponse
from src.api.deps import get_subagent_manager,get_message_queue_manager
from src.runtime.message_queue import MessageQueueManager
from src.sub_agents.subagent_manager import SubAgentManager
from src.runtime.message_queue import QueueRequest
import json
import uuid
from loguru import logger

# 创建路由实例（v1版本）
router = APIRouter(prefix="/v1/agent", tags=["agent"])

@router.post('/chat', summary="Chat with agent")
async def chat(
    response:Response,
    message: str = Body(..., embed=False, description="用户消息内容"),
    agent_id: str = Body("main", description="Agent ID"),
    stream: bool = Body(False, description="是否使用流式响应"),
    message_queue_manager:MessageQueueManager=Depends(get_message_queue_manager),
    session_manager: SessionManager = Depends(get_session_manager),
    raw_session_id: Optional[str] = Cookie(None, alias="chat_session_id"),
    session_id: Optional[str] = Body(None, description="Client session_id"),

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
        logger.warning("空消息串")
        raise HTTPException(status_code=400, detail="Message is empty")

    incoming_session_id = session_id or raw_session_id
    logger.info(f"输入session_id: {incoming_session_id}")
    session_id = await session_manager.get_session_id(
        session_id=incoming_session_id,
        response=response,
    )

    #创建请求id
    request_id=uuid.uuid4().hex

    # 如果请求流式响应
    if stream:
        raise HTTPException(
            status_code=400,
            detail="Stream response is not supported yet"
        )

    # 非流式响应
    else:
        request=QueueRequest(
            request_id=request_id,
            message=message,
            agent_id=agent_id,
            session_id=session_id,
            stream=False
        )

        result=await message_queue_manager.submit(request)
        logger.info(f"请求结果类型: {result['type']}")
    if result["type"] == "queued":
        return ChatResponse(
            code=202,
            message="queued",
            data={
                "session_id": session_id,
                "agent_id": agent_id,
                "position": result["position"],
                "detail": result["message"],
                'request_id':request_id
            },
        )

    if result["type"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])

    if result["type"] == "aborted":
        return ChatResponse(
            code=200,
            message="aborted",
            data={
                "session_id": session_id,
                "agent_id": agent_id,
                "response": result["content"],
                "reason": result["reason"],
            },
        )

    return ChatResponse(
        code=200,
        message="success",
        data={
            "session_id": session_id,
            "agent_id": agent_id,
            "response": result["content"],
        },
    )

@router.post('/multi-chat',summary='Run multi-agent tasks')
async def multi_chat(
    messages:str=Body(...,embed=False,description='用户消息内容'),
    agent_id: str = Body("main", description="Agent ID"),
    subagent_manager: SubAgentManager = Depends(get_subagent_manager),
    session_manager: SessionManager = Depends(get_session_manager),
    raw_session_id: Optional[str] = Cookie(None, alias="chat_session_id"),
    response: Response = None,
):
    message=messages.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")
    
    #获取会话id，设置cookie
    session_id=session_manager.get_session_id(
        session_id=raw_session_id,
        response=response
    )

    #获取历史上下文

    # 获取子任务
    tasks = [
        f"请从架构角度分析这个问题：{message}",
        f"请从实现细节角度分析这个问题：{message}",
        f"请从风险和改进建议角度分析这个问题：{message}",
    ]

    results = await subagent_manager.run_parallel_tasks(
        parent_session_id=session_id,
        tasks=tasks,
        agent_id=agent_id,
    )


    task_results = []
    summary_parts = []

    for item in results:
        task_results.append({
            "task_id": item.task_id,
            "label": item.label,
            "task": item.task,
            "status": item.status,
            "result": item.result,
            "error": item.error,
            "child_session_id": item.child_session_id,
        })

        if item.status == "completed" and item.result:
            summary_parts.append(f"[{item.label}]\\n{item.result}")
        elif item.status == "failed":
            summary_parts.append(f"[{item.label}] 失败: {item.error}")
    return ChatResponse(
        code=200,
        message="success",
        data={
            "session_id": session_id,
            "agent_id": agent_id,
            "tasks": task_results,
            "summary": "\\n\\n".join(summary_parts),
        },
    )

@router.post('/abort',summary='Abort a session')
async def abort_chat(
    response: Response,
    session_manager:SessionManager=Depends(
        get_session_manager
    ),
    message_queue_manager:MessageQueueManager=Depends(get_message_queue_manager),
    raw_session_id: Optional[str] = Cookie(None, alias="chat_session_id"),
    session_id: Optional[str] = Body(None, description="Client session_id"),

):
    incoming_session_id = session_id or raw_session_id
    resolved_session_id = await session_manager.get_session_id(
        session_id=incoming_session_id,
        response=response,
    )

    result = await message_queue_manager.abort(session_id=resolved_session_id)

    return ChatResponse(
        code=200,
        message="success",
        data=result
    )
@router.get("/chat/result", summary="Get queued request result")
async def get_chat_result(
    request_id: str,
    message_queue_manager: MessageQueueManager = Depends(get_message_queue_manager),
):
    state = message_queue_manager.get_request_state(request_id)
    return ChatResponse(code=200, message="success", data=state)


@router.post("/chat/stream", summary="Chat with agent (stream)")
async def chat_stream(
    response: Response,
    message: str = Body(..., embed=False, description="用户消息内容"),
    agent_id: str = Body("main", description="Agent ID"),
    session_id: Optional[str] = Body(None, description="Client session_id"),
    raw_session_id: Optional[str] = Cookie(None, alias="chat_session_id"),
    session_manager: SessionManager = Depends(get_session_manager),
    message_queue_manager: MessageQueueManager = Depends(get_message_queue_manager),
    agent_manager: AgentManager = Depends(get_agent_manager),
):
    message = message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty")

    incoming_session_id = session_id or raw_session_id
    resolved_session_id = await session_manager.get_session_id(
        session_id=incoming_session_id,
        response=response,
    )

    # v1: 流式只允许在空闲 session 上执行，避免和队列并发冲突
    runtime = message_queue_manager.get_runtime(resolved_session_id)
    if runtime.is_busy:
        raise HTTPException(
            status_code=409,
            detail="Session is busy. Use /chat (non-stream) to queue.",
        )

    async def generate():
        try:
            async for event in agent_manager.astream(
                message=message,
                session_id=resolved_session_id,
                agent_id=agent_id,
            ):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
