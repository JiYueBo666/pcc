from __future__ import annotations
from typing import List
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from src.schemas.users import (
    UserInfoRequest,
    UserInfoResponse,
)
from src.userInfo import UserSessionManager
from src.api.deps import get_user_manager

router=APIRouter(prefix="/v1/user",tags=["user"])


@router.get('/sessions',response_model=UserInfoResponse,summary='查找会话ID')
async def get_user_info(username:str=Query(default=None,description='用户名'),
                        um:UserSessionManager=Depends(get_user_manager)):
    try:
        sessions=um.get_user_sessions(username)
        msg=f"查询到{len(sessions)}个会话ID" if sessions else "暂无会话ID"
        if username and username.strip():
            msg=f'用户【{username}】,{msg}'
        return UserInfoResponse(
            code=200,
            msg=msg,
            data=sessions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

