from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Response


class SessionManager:  # 规范命名：大驼峰+无下划线
    """Session业务服务层"""
    def __init__(self):
        pass
    
    # 改为实例方法，接收接口层传过来的原始值
    async def get_session_id(
        self,
        session_id: Optional[str],  # 接口层从Cookie读的原始值
        response: Response          # 接口层的Response对象
    ) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())
            response.set_cookie(
                key="chat_session_id",
                value=session_id,
                max_age=60*60*24*7,
                httponly=True,
                samesite="lax"
            )
        return session_id