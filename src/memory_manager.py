'''
#核心记忆管理
'''

from __future__ import annotations
import datetime
import json
from pathlib import Path
from typing import Literal, Generator, List, Dict
from dataclasses import dataclass, asdict
from loguru import logger
from src.config import config

@dataclass
class MemoryItem:
    content:str
    session_id:str
    role:Literal['user','assistant','system']
    created_at:datetime.datetime

    def to_dict(self):
        #转化为可序列化字典
        data=asdict(self)
        data['created_at']=data['created_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls,data:Dict):
        #从字典还原对象
        data['created_at']=datetime.datetime.fromisoformat(data['created_at'])
        return cls(**data)

class MemoryManager:
    '''
    工程化CRUD
    '''
    def __init__(self):
        self.storage_dir=config.MEMORY_STORAGE_DIR
        self.max_message=config.MAX_MESSAGES_PER_SESSION
    def _get_session_file(self,session_id:str):
        return self.storage_dir / f'{session_id}.jsonl'
    
    def add_memory(self,content:str,session_id:str,role:Literal['user','assistant']):
        '''
        添加记忆
        '''
        #入参检验
        if not content.strip():
            raise ValueError('content不能为空')
        if not session_id.strip():
            raise ValueError("会话ID不能为空")
        if role not in ["user", "system", "assistant"]:
            raise ValueError(f"非法角色：{role}，仅支持user/system")
        
        #创建记忆项
        memory=MemoryItem(
            content=content.strip(),
            session_id=session_id,
            role=role,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )

        #写入文件 json line 追加
        session_file=self._get_session_file(session_id)
        try:
            #检查会话消息数
            existing_count=len(list(self.get_memories(session_id)))
            if existing_count>=self.max_message:
                logger.warning(f"会话{session_id}消息数已达到最大值{self.max_message}，删除最早消息")
                self._truncate_oldest_message(session_id)
            with open(session_file,'a',encoding='utf-8') as f:
                f.write(json.dumps(memory.to_dict(),ensure_ascii=False)+'\n')
            logger.info(f"会话{session_id}添加记忆成功,内容{content[:20]}...")
            return memory
        except OSError as e:
            logger.error(f"会话{session_id}添加记忆失败，错误信息{e}")
            raise RuntimeError(f"会话{session_id}添加记忆失败，错误信息{e}")
    def get_memories(self,session_id:str):
        session_file=self._get_session_file(session_id)
        if not session_file.exists():
            logger.debug(f"会话{session_id}不存在")
            return 
        try:
            with open(session_file,'r',encoding='utf-8') as f:
                for line in f:
                    line=line.strip()
                    if not line:
                        continue
                    try:
                        data=json.loads(line)
                        yield MemoryItem.from_dict(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"会话{session_id}读取记忆失败，错误信息{e}")
                        continue
        except OSError as e:
            logger.error(f"会话{session_id}读取记忆失败，错误信息{e}")
            raise RuntimeError(f"会话{session_id}读取记忆失败，错误信息{e}")
    def delete_memories(self,session_id:str,delete_all:bool=False,content:str=None):
        session_file=self._get_session_file(session_id)
        if not session_file.exists():
            logger.info(f"会话{session_id}不存在,无需删除")
            return True
        try:
            if delete_all:
                session_file.unlink()#直接删除文件
                logger.info(f"会话{session_id}删除成功")
                return True
            else:
                if not content:
                    raise ValueError("删除记忆时必须指定content")
                remaining_memories=[]
                for memory in self.get_memories(session_id):
                    if content not in memory.content:
                        remaining_memories.append(memory)
                # 重新写入
                with open(session_file, "w", encoding="utf-8") as f:
                    for mem in remaining_memories:
                        f.write(json.dumps(mem.to_dict(), ensure_ascii=False) + "\n")
                logger.info(f"会话{session_id}删除包含'{content}'的记忆，剩余{len(remaining_memories)}条")
                return True
        except OSError as e:
            logger.error(f"会话{session_id}删除记忆失败：{str(e)}")
            raise RuntimeError(f"删除记忆失败：{str(e)}") from e
    def _truncate_oldest_message(self,session_id:str):
        session_file = self._get_session_file(session_id)
        memories = list(self.get_memories(session_id))
        if len(memories) == 0:
            return
        
        # 保留除第一条外的所有消息
        remaining = memories[1:]
        with open(session_file, "w", encoding="utf-8") as f:
            for mem in remaining:
                f.write(json.dumps(mem.to_dict(), ensure_ascii=False) + "\n")