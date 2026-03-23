from __future__ import annotations
from typing import Any
from langchain_core.tools import BaseTool
from pydantic import BaseModel,Field

class SessionsSpawnInput(BaseModel):
    task: str = Field(description="子 Agent 要执行的任务描述")
    agent_id: str = Field(default="", description="目标 Agent ID（默认当前 Agent）")
    label: str | None = Field(default=None, description="子 Agent 标签（可选）")
    model: str | None = Field(default=None, description="模型覆盖（可选）")


class SessionSpawnTool(BaseTool):
    name:str='sessions_spawn'
    description:str=(
        "在后台启动一个独立的子 Agent 执行任务。子 Agent 完成后会自动通知。"
    )
    args_schema:type[BaseModel]=SessionsSpawnInput
    current_agent_id: str = "main"
    current_session_id: str = ""
    _agent_manager: Any = None
    _main_loop: Any = None
    _FAILURE_HINTS = (
        "failure",
        "error",
        "exception",
        "timeout",
        "not found",
        "return none",
        "no results",
        "cannot",
        "failed",
        "无结果",
        "无法",
        "失败",
    )

    def _run(
            self,
            task: str,
            agent_id: str = "",
            label: str | None = None,
            model: str | None = None,
    ):
        target_id=agent_id or self.current_agent_id

        #权限校验
        requester_id=self.current_agent_id or 'main'
        requester_cfg=resolve_agent_config(requester_id) or {}

def get_agent_tools(
        agent_id:str,
        agent_manager:Any=None,
        session_id:str='',
        main_loop:Any=None,
):
    spawn_tool=SessionSpawnTool(
        current_agent_id=agent_id,
        current_session_id=session_id,
    )
    spawn_tool._agent_manager=agent_manager
    spawn_tool._main_loop=main_loop
