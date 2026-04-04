from __future__ import annotations  # 启用Python的未来类型注解功能，允许在Python 3.9及以下版本中使用类型注解
import asyncio  # 异步IO库，用于实现异步编程
from typing import Dict  # 字典类型，用于类型注解
from loguru import logger
from src.agent.agent_manager import AgentManager  # 从agent模块导入AgentManager类，用于管理代理
from src.memory.memory_manager import MemoryManager  # 从memory模块导入MemoryManager类，用于管理内存
from src.runtime.session_runtime import QueueRequest,SessionRuntime  # 从runtime模块导入QueueRequest和SessionRuntime类，用于处理会话运行时

class MessageQueueManager:
    '''
    消息队列管理器，为会话保存独立的SessionRuntime
    '''
    def __init__(self,agent_manager:AgentManager,memory_manager:MemoryManager):
        """
        初始化MessageQueueManager类
        :param agent_manager: AgentManager实例，用于管理代理
        :param memory_manager: MemoryManager实例，用于管理内存
        """
        self.agent_manager=agent_manager
        self.memory_manager=memory_manager 
        self._runtimes:Dict[str,SessionRuntime]={}  # 存储会话运行时的字典，键为session_id
        self._request_results:Dict[str,dict]={}
    def get_runtime(self,session_id:str):
        """
        获取指定session_id的SessionRuntime实例，如果不存在则创建一个新的
        :param session_id: 会话ID
        :return: SessionRuntime实例
        """
        runtime=self._runtimes.get(session_id)  # 从字典中获取运行时实例
        if runtime is None:  # 如果不存在，则创建一个新的
            runtime=SessionRuntime(session_id=session_id)  # 创建新的运行时实例
            self._runtimes[session_id]=runtime  # 存储到字典中
        return runtime  # 返回运行时实例


    async def _emit(self,request:QueueRequest,event:dict):
        '''
        将生成好的数据块放入队列
        '''
        if request.stream and request.event_queue is not None:
            await request.event_queue.put(event)  # 将事件放入事件队列中
    
    async def submit(self,request:QueueRequest):
        """
        提交请求到消息队列
        :param request: QueueRequest实例，包含请求信息
        :return: 包含请求处理结果的字典
        """
        runtime=self.get_runtime(request.session_id)  # 获取或创建运行时实例

        self._set_request_state(
            request.request_id,
            'pending',
            session_id=request.session_id
        )

        async with runtime.lock:
            if runtime.is_busy:  # 检查运行时是否忙碌
                runtime.pending_requests.append(request)  # 将请求添加到待处理队列
                self._set_request_state(
                    request.request_id,
                    'queued',
                    session_id=request.session_id,
                    position=len(runtime.pending_requests),
                )
                logger.info(f"会话忙，插入请求队列,位置:{len(runtime.pending_requests)}")
                await self._emit(
                    request,
                    {
                        "type": "queued",
                        'request_id':request.request_id,
                        'position':len(runtime.pending_requests),
                        'message':"请求入队，因为会话忙碌"
                    },
                )
                return {
                    'type': 'queued',
                    'session_id':request.session_id,
                    'position':len(runtime.pending_requests),
                    'message':"请求入队，因为会话忙碌"
                }
        logger.info("会话空闲，运行请求")
        return await self._run_request(runtime,request)  # 如果不忙碌，直接运行请求
    async def abort(self,session_id:str):
        """
        中止指定session_id的请求
        :param session_id: 会话ID
        :return: 包含中止结果的字典
        """
        runtime=self.get_runtime(session_id)  # 获取或创建运行时实例

        async with runtime.lock:
            cleared_queue=len(runtime.pending_requests)

            #通知排队中的streamlit请求被取消
            while runtime.pending_requests:
                req=runtime.pending_requests.popleft()
                self._set_request_state(
                    req.request_id,
                    'aborted',
                    session_id=req.session_id,
                    reason='用户终止'
                )

                await self._emit(
                    req,
                    {
                        "type": "aborted",
                        'request_id':req.request_id,
                        'reason':"请求被取消"
                    }
                )
            if runtime.active_task is None or runtime.active_task.done():
                return {
                    "aborted": False,
                    "session_id": session_id,
                    "cleared_queue": cleared_queue,
                    "partial_output": "",
                }
            runtime.user_aborted=True
            runtime.active_task.cancel()
        try:
            await runtime.active_task
        except asyncio.CancelledError:
            pass
        return {
            "aborted": True,
            "session_id": session_id,
            "cleared_queue": cleared_queue,
            "partial_output": runtime.partial_output,
        }


    async def _run_request(
            self,runtime:SessionRuntime,
            request:QueueRequest
    ):
        runtime.is_busy=True
        runtime.partial_output=''
        runtime.user_aborted=False

        self._set_request_state(
            request.request_id,
            "running",
            session_id=request.session_id,
        )

        #嵌套函数，可以直接访问外部函数变量
        async def runner():
            try:
                async for event in self.agent_manager.astream(
                    message=request.message,
                    session_id=request.session_id,
                    agent_id=request.agent_id,
                ):
                    event_type=event.get('type')

                    if event_type == "token":
                        token=event.get("content", "")
                        runtime.partial_output += token
                        await self._emit(
                            request,
                            {
                                "type": "token",
                                'content':token,
                                'request_id':request.request_id,
                            }
                        )
                    elif event_type=='tool_start':
                        await self._emit(
                            request,
                            {
                                'type':'tool_start',
                                'request_id':request.request_id,
                                'tool_name':event.get('tool_name'),
                                'tool_input':event.get('tool_input'),
                            }
                        )
                    elif event_type=='tool_end':
                        await self._emit(
                            request,
                            {
                                'type':'tool_end',
                                'request_id':request.request_id,
                                'tool_output':event.get('tool_output'),
                            }
                        )

                    elif event_type == "error":
                        err=event.get('error','UnKnow error')
                        self._set_request_state(
                        request.request_id,
                        "error",
                        session_id=request.session_id,
                        error=err,
                        partial_output=runtime.partial_output,
                    )
                        await self._emit(
                            request,
                            {
                                "type": "error",
                                'request_id':request.request_id,
                                'error':err,
                                'partial_output':runtime.partial_output,
                            }
                        )

                        return {
                                "type": "error",
                                "session_id": request.session_id,
                                "error": err,
                                "partial_output": runtime.partial_output,
                            }
                    
                self._set_request_state(
                request.request_id,
                "done",
                session_id=request.session_id,
                content=runtime.partial_output,
            )
                await self._emit(
                        request,
                        {
                            "type": "done",
                            'request_id':request.request_id,
                            'content':runtime.partial_output,
                        }
                )
                return {
                        "type": "done",
                        "session_id": request.session_id,
                        "content": runtime.partial_output,
                    }
            except asyncio.CancelledError:
                if runtime.partial_output.strip():
                    await self.memory_manager.add_memory(
                        content=runtime.partial_output,
                        session_id=request.session_id,
                        role="assistant",
                    )

                self._set_request_state(
                    request.request_id,
                    "aborted",
                    session_id=request.session_id,
                    content=runtime.partial_output,
                    reason="stopped_by_user",
                )
                await self._emit(
                    request,
                    {
                        "type": "aborted",
                        "request_id": request.request_id,
                        "content": runtime.partial_output,
                        "reason": "stopped_by_user",
                    },
                )
                return {
                    "type": "aborted",
                    "session_id": request.session_id,
                    "content": runtime.partial_output,
                    "reason": "stopped_by_user",
                }
        
        task=asyncio.create_task(runner())
        
        runtime.active_task=task
        try:
            result=await task
            return result
        finally:
            runtime.active_task=None
            runtime.is_busy=False

            should_continue=(
                not runtime.user_aborted and
                len(runtime.pending_requests)>0
            )

            runtime.user_aborted=False

            # 如果需要继续执行
            if should_continue:
                # 检查drain_task是否为None或已经完成
                if runtime.drain_task is None or runtime.drain_task.done():
                # 如果drain_task不存在或已完成，则创建一个新的异步任务来执行_drain_queue方法
                    runtime.drain_task=asyncio.create_task(
                        self._drain_queue(runtime)  # 调用_drain_queue方法，并将runtime作为参数传入
                    )
    async def _drain_queue(self, runtime: SessionRuntime) -> None:
        while True:
            async with runtime.lock:
                if runtime.is_busy or not runtime.pending_requests:
                    return
                next_request = runtime.pending_requests.popleft()

            await self._run_request(runtime, next_request)
    def _set_request_state(self, request_id: str, state: str, **extra) -> None:
        self._request_results[request_id] = {"state": state, **extra}

    def get_request_state(self, request_id: str) -> dict:
        return self._request_results.get(request_id, {"state": "not_found"})
