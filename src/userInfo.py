from __future__ import annotations
import json
from pathlib import Path
from typing import List,Dict,Optional
from loguru import logger
from src.config import config


class UserSessionManager:
    def __init__(self):
        self.mapping_file=config.MEMORY_STORAGE_DIR/'user_session_mapping.json'
        self._mapping:Dict[str,List[str]]=self._load_mapping()
    
    def _load_mapping(self):
        try:
            if self.mapping_file.exists():
                with open(self.mapping_file,'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f'加载用户会话映射失败: {e}')
            return {}
    def _save_mapping(self):
        try:
            with open(self.mapping_file, "w", encoding="utf-8") as f:
                json.dump(self._mapping, f, ensure_ascii=False, indent=2)
            logger.info("用户-会话映射已保存")
        except Exception as e:
            logger.error(f"保存用户-会话映射失败：{e}")
            raise RuntimeError(f"保存用户-会话映射失败：{e}")
    def bind_session_to_user(self, username: str, session_id: str) -> None:
        """绑定会话ID到指定用户（去重）"""
        if not username or not session_id:
            raise ValueError("用户名和会话ID不能为空")
        
        # 统一用户名格式（小写，去空格）
        username = username.strip().lower()
        
        if username not in self._mapping:
            self._mapping[username] = []
        
        # 去重
        if session_id not in self._mapping[username]:
            self._mapping[username].append(session_id)
            self._save_mapping()
    def get_user_sessions(self, username: Optional[str] = None) -> List[str]:
        """
        获取用户的会话ID列表
        :param username: 用户名（空则返回所有会话ID）
        :return: 会话ID列表（去重、排序）
        """
        # 1. 获取所有已存储的会话ID（从映射+记忆文件双重获取）
        all_sessions = set()
        
        # 从用户-会话映射中获取所有会话ID
        for sessions in self._mapping.values():
            all_sessions.update(sessions)
        
        # 从记忆文件中补充会话ID（避免映射文件缺失的情况）
        memory_files = config.MEMORY_STORAGE_DIR.glob("*.jsonl")
        for file in memory_files:
            session_id = file.stem  # 记忆文件名为session_id.jsonl
            all_sessions.add(session_id)
        
        # 2. 按用户名过滤
        if username and username.strip():
            username = username.strip().lower()
            user_sessions = self._mapping.get(username, [])
            # 过滤出该用户的会话ID（同时存在于所有会话中）
            result = [s for s in user_sessions if s in all_sessions]
        else:
            # 用户名空，返回所有会话ID
            result = list(all_sessions)
        
        # 3. 排序（按创建时间倒序，会话ID含时间戳时生效）
        result.sort(reverse=True)
        return result

