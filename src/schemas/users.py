from __future__ import annotations

from pydantic import BaseModel, Field


class UserInfoRequest(BaseModel):
    username: str | None = Field(default=None, description="用户名")


class UserInfoResponse(BaseModel):
    code: int = Field(default=200, description="返回状态码")
    message: str | None = Field(default=None, description="返回信息")
    data: list[str] = Field(default_factory=list, description="返回数据")
