from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class Config:
    '''全局配置类（扩展FastAPI服务配置）'''
    # ========== 原有配置（阶段1） ==========
    MEMORY_STORAGE_DIR = Path(os.getenv('MEMORY_STORAGE_DIR', './data/memories'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", 1000))

    # ========== 新增：FastAPI服务配置 ==========
    API_HOST = os.getenv('API_HOST', '0.0.0.0')  # 允许外部访问
    API_PORT = int(os.getenv('API_PORT', 8000))
    API_DEBUG = os.getenv('API_DEBUG', 'True').lower() == 'true'  # 调试模式
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')  # 跨域允许的源

    @classmethod
    def init_dirs(cls):
        # 原有逻辑（不变）
        cls.MEMORY_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        log_dir = Path('./logs')
        log_dir.mkdir(exist_ok=True)

        # 配置日志
        logger.remove()
        logger.add(
            './logs/memory_tool.log',
            level=cls.LOG_LEVEL,
            rotation='10MB',
            retention='7 days',
            encoding='utf-8',
            enqueue=True
        )
        logger.add(
            lambda msg: print(msg, end=''),
            level=cls.LOG_LEVEL,
            colorize=True,
        )

# 全局唯一实例
config = Config()
config.init_dirs()