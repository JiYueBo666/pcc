from __future__ import annotations
import os
from pathlib  import Path
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

class Config:
    '''
    全局配置类
    '''

    #存储目录
    MEMORY_STORAGE_DIR=Path(os.getenv('MEMORY_STORAGE_DIR','./data/memories'))
    #日志级别
    LOG_LEVEL=os.getenv('LOG_LEVEL','INFO').upper()
    #单个会话最大消息数
    MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", 1000))

    @classmethod
    def init_dirs(cls):
        cls.MEMORY_STORAGE_DIR.mkdir(parents=True,exist_ok=True)
        #创建日志目录
        log_dir=Path('./logs')
        log_dir.mkdir(exist_ok=True)

        #配置日志
        logger.remove()
        logger.add(
            './logs/memory_tool.log',
            level=cls.LOG_LEVEL,
            rotation='10MB',#日志超过10MB则分割
            retention='7 days',
            encoding='utf-8',
            enqueue=True
        )
        #控制台输出日志
        logger.add(
            lambda msg:print(msg,end=''),
            level=cls.LOG_LEVEL,
            colorize=True,
        )

config=Config()
config.init_dirs()

        