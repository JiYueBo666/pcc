from __future__ import annotations  # 启用Python的未来类型注解功能，允许在Python 3.9及以下版本中使用类型注解
import asyncio  # 异步IO库，用于实现异步编程
from typing import Dict  # 字典类型，用于类型注解
from loguru import logger
from src.agent.agent_manager import AgentManager  # 从agent模块导入AgentManager类，用于管理代理
from src.memory.memory_manager import MemoryManager  # 从memory模块导入MemoryManager类，用于管理内存
from src.runtime.session_runtime import QueueRequest,SessionRuntime  # 从runtime模块导入QueueRequest和SessionRuntime类，用于处理会话运行时

class MessageQueueManager:
    def __init__(self,agent_manager:AgentManager,memory_manager:MemoryManager):
        """
        初始化MessageQueueManager类
        :param agent_manager: AgentManager实例，用于管理代理
        :param memory_manager: MemoryManager实例，用于管理内存
        """
        self.agent_manager=agent_manager  # 存储AgentManager实例
        self.memory_manager=memory_manager  # 存储MemoryManager实例
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

    async def submit(self,request:QueueRequest):
        """
        提交请求到消息队列
        :param request: QueueRequest实例，包含请求信息
        :return: 包含请求处理结果的字典
        """
        runtime=self.get_runtime(request.session_id)  # 获取或创建运行时实例

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
                return {  # 返回队列状态信息
                    'type':'queued',
                    'session_id':request.session_id,
                    'position':len(runtime.pending_requests),
                    'request_id':request.request_id,
                    'message':'Request queued because this session is busy'
                }
        logger.info("会话空闲，运行请求")
        self._set_request_state(request.request_id, "running", session_id=request.session_id)
        return await self._run_request(runtime,request)  # 如果不忙碌，直接运行请求
    async def abort(self,session_id:str):
        """
        中止指定session_id的请求
        :param session_id: 会话ID
        :return: 包含中止结果的字典
        """
        runtime=self.get_runtime(session_id)  # 获取或创建运行时实例

        cleared_queue=len(runtime.pending_requests)  # 记录已清除的队列长度
        # 清空待处理请求队列
        runtime.pending_requests.clear()
        if runtime.active_task is None or runtime.active_task.done():
            return {
                "aborted": False,
                "session_id": session_id,
                "cleared_queue": cleared_queue,
                "partial_output": "",
            }
        runtime.user_aborted=True  # 标记用户中止
        runtime.active_task.cancel()  # 取消当前任务

        try:
            result=await runtime.active_task
        except asyncio.CancelledError:
            result={
                'type':"aborted",
                'session_id':session_id,
                'content':runtime.partial_output,
                'reason':'stopped_by_user'
            }
        return {
            'aborted':True,
            'session_id':session_id,
            'cleared_queue':cleared_queue,
            'partial_output':runtime.partial_output,
            'result':result
        }
    async def _run_request(
            self,runtime:SessionRuntime,
            request:QueueRequest
    ):
        runtime.is_busy=True

        self._set_request_state(
    request.request_id,
    "running",
    session_id=request.session_id,
)
        runtime.partial_output=''
        runtime.user_aborted=False

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
                            runtime.partial_output += event.get("content", "")

                    elif event_type == "error":
                        self._set_request_state(
                        request.request_id,
                        "error",
                        session_id=request.session_id,
                        error=event.get("error", "Unknown error"),
                        partial_output=runtime.partial_output,
                    )

                        return {
                                "type": "error",
                                "session_id": request.session_id,
                                "error": event.get("error", "Unknown error"),
                                "partial_output": runtime.partial_output,
                            }
                self._set_request_state(
                request.request_id,
                "done",
                session_id=request.session_id,
                content=runtime.partial_output,
            )

                return {
                        "type": "done",
                        "session_id": request.session_id,
                        "content": runtime.partial_output,
                    }
            except asyncio.CancelledError:
                self._set_request_state(
                request.request_id,
                "aborted",
                session_id=request.session_id,
                content=runtime.partial_output,
                reason="stopped_by_user",
            )

                if runtime.partial_output.strip():
                    await self.memory_manager.add_memory(
                        content=runtime.partial_output,
                        session_id=request.session_id,
                        role='assistant',
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
        while runtime.pending_requests and not runtime.is_busy:
            next_request = runtime.pending_requests.popleft()
            await self._run_request(runtime, next_request)
    def _set_request_state(self, request_id: str, state: str, **extra) -> None:
        self._request_results[request_id] = {"state": state, **extra}

    def get_request_state(self, request_id: str) -> dict:
        return self._request_results.get(request_id, {"state": "not_found"})
