from __future__ import annotations
from loguru import logger
from typing import Any
from langchain_openai import ChatOpenAI
from src.agent.model_config import ModelRef

def create_llm(ref:ModelRef,temerature:float=0.9,streaming:bool=True):
    '''
    只创建openai类模型
    '''
    return _create_openai(ref,temerature,streaming)

def _create_openai(ref:ModelRef,temperature:float=0.9,streaming:bool=True):
    api_key,base_url=ref.api_key,ref.base_url
    model_id=ref.model_id
    kwargs: dict[str, Any] = {
        "api_key": api_key,
        "model": model_id,
        "base_url":base_url,
        "temperature": temperature,
        "streaming": streaming,
    }
    return ChatOpenAI(**kwargs)

class LLMCache:
    def __init__(self):
        self._cache:dict={}
    def get_or_create(self,agent_id:str,ref:ModelRef,streaming:bool=True):
        cached=self._cache.get(agent_id)
        if cached:
            return cached
        llm=create_llm(ref)
        self._cache[agent_id]=llm
        logger.info(f'create llm for agent {agent_id}')
        return llm
    def invalidate(self,agent_id:str):
        self._cache.pop(agent_id,None)
    def invalidate_all(self) -> None:
        self._cache.clear()

    def get_current_ref(self, agent_id: str) -> ModelRef | None:
        cached = self._cache.get(agent_id)
        return cached[0] if cached else None

llm_cache = LLMCache()