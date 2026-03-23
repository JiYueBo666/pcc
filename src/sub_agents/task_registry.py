from __future__ import annotations
from typing import Dict,List,Optional
import time
from src.sub_agents.schemas import SubTaskRecord

class TaskRegistry:
    def __init__(self):
        self._tasks:Dict[str,SubTaskRecord]={}
    def create_task(
            self,
            task_id:str,
            parent_session_id:str,
            child_session_id:str,
            agent_id:str,
            task:str,
            label:str|None=None
    ):
        record=SubTaskRecord(
            task_id=task_id,
            parent_session_id=parent_session_id,
            child_session_id=child_session_id,
            agent_id=agent_id,
            task=task,
            label=label,
        )
        self._tasks[task_id]=record
        return record
    def get_task(self,task_id:str)->Optional[SubTaskRecord]:
        return self._tasks.get(task_id,None)
    def list_by_parent_session(self,parent_session_id:str)->List[SubTaskRecord]:
        return  [
            task for task in self._tasks.values()
            if task.parent_session_id==parent_session_id
        ]
    def mark_running(self,task_id:str):
        task=self._tasks[task_id]
        task.status='running'
        task.started_at=time.time()
    def mark_completed(self,task_id:str,result):
        task=self._tasks[task_id]
        task.status='completed'
        task.result=result
        task.ended_at=time.time()
    def mark_failed(self,task_id:str,err:str):
        task=self._tasks[task_id]
        task.status='failed'
        task.error=err
        task.ended_at=time.time()