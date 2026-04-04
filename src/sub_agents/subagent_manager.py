from __future__ import annotations
import asyncio
import uuid
from typing import List
from src.agent.agent_manager import AgentManager
from src.sub_agents.task_registry import TaskRegistry
from src.sub_agents.schemas import SubTaskRecord

class SubAgentManager:
    def __init__(self,agent_manager:AgentManager,
                task_registry:TaskRegistry,
                ):
        self.agent_manager = agent_manager
        self.task_registry = task_registry
    async def run_subtask(
            self,parent_session_id:str,
            task:str,
            agent_id:str='main',
            label:str|None=None
    ):
        task_id=uuid.uuid4().hex
        child_session_id = f"sub-{uuid.uuid4().hex}"
        record=self.task_registry.create_task(
            task_id=task_id,
            parent_session_id=parent_session_id,
            child_session_id=child_session_id,
            agent_id=agent_id,
            task=task,
            label=label
        )
        self.task_registry.mark_running(task_id=task_id)
        full_response=''
        try:
            async for event in self.agent_manager.astream(
                message=task,
                session_id=child_session_id,
                agent_id=agent_id
            ):
                if event.get("type") == "token":
                    full_response += event.get("content", "")
                elif event.get("type") == "error":
                    raise RuntimeError(event.get("error", "subtask failed"))
            self.task_registry.mark_completed(task_id,full_response)
        except Exception as e:
            self.task_registry.mark_failed(task_id,str(e))
        return self.task_registry.get_task(task_id)
    async def run_parallel_tasks(
            self,
            parent_session_id:str,
            tasks:List[str],
            agent_id:str='main',
    ):
        #收集协程对象
        coroutines=[
            self.run_subtask(
                parent_session_id=parent_session_id,
                task=task,
                agent_id=agent_id,
                label=f"subtask-{index+1}",
            )
            for index,task in enumerate(tasks)
        ]
        results=await asyncio.gather(*coroutines)
        return results