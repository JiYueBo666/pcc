from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import v1_router
from src.core.config import config

app = FastAPI(
    title="Memory Tool API",
    description="本地记忆与 Agent 交互服务",
    version="1.0.0",
    debug=config.API_DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api")

@app.get("/", summary="健康检查")
def health_check():
    return {
        "status": "healthy",
        "service": "memory-tool-api",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_DEBUG,
    )
