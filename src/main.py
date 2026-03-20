from __future__ import annotations
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import config
from src.api import v1_router

# 创建FastAPI应用实例
app = FastAPI(
    title="Memory Tool API",
    description="阶段2：FastAPI接口化记忆工具（基于阶段1本地存储）",
    version="1.0.0",
    debug=config.API_DEBUG
)


# 配置跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(v1_router, prefix="/api")

# 根路径健康检查
@app.get("/", summary="健康检查")
def health_check():
    return {
        "status": "healthy",
        "service": "memory-tool-api",
        "version": "1.0.0"
    }

# 启动服务
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.API_DEBUG  # 调试模式下自动重载
    )