from src.agent.model_selection import resolve_agent_model
from src.tools.file_tools import _read_file
from langchain.messages import HumanMessage,AIMessage,SystemMessage
from loguru import logger
from src.memory_manager import MemoryManager,MemoryItem
class AgentManager:
    def __init__(self):
        self.memory_manager = MemoryManager()


    def get_llm(self,agent_id:str='main'):
        #通过agent id，从缓存中获取llm，或者创建llm
        #单llm暂不考虑agent id，统一为main
        from src.agent.llm_factory import llm_cache
        #从agent id解析模型配置
        ref=resolve_agent_model(agent_id)
        return llm_cache.get_or_create(agent_id,ref)
    
    def _build_tools(self,agent_id:str='main',session_id:str=""):
        tools=[]
        tools.append(_read_file)
        return tools

    async def astream(
            self,
            message: str,
            session_id: str,
            agent_id: str = "main"
    ):
        """
        流式处理Agent对话，返回生成器

        参数:
            message: 用户消息
            session_id: 会话ID
            agent_id: Agent ID

        返回:
            异步生成器，产生流式响应数据
        """
        # 保存用户消息到memory
        await self.memory_manager.add_memory(
            content=message,
            session_id=session_id,
            role="user"
        )

        # 构建工具列表
        tools = self._build_tools(agent_id, session_id)

        # 构建系统提示词
        # TODO: 获取系统提示词
        system_prompt = "You are a helpful assistant with access to tools."

        #获取历史记录
        history=list(await self.memory_manager.get_memories(session_id=session_id))

        # 构建消息列表
        messages = self._build_messages(history,message)

        from langchain.agents import create_agent
        # 获取LLM实例
        llm = self.get_llm(agent_id)

        # 创建代理
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )

        # 用于收集完整的助手回复
        full_assistant_response = ""

        # 执行流式调用处理事件
        try:
            async for event in agent.astream_events(
                {"messages": messages},
                version='v2',
                config={"recursion_limit": 50}
            ):
                kind = event.get("event", "")

                # 处理流式文本输出
                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        content = chunk.content
                        full_assistant_response += content
                        yield {
                            "type": "token",
                            "content": content
                        }

                # 处理工具调用开始
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    tool_input = event.get("data", {}).get("input") or {}
                    yield {
                        "type": "tool_start",
                        "tool_name": tool_name,
                        "tool_input": tool_input
                    }
                    logger.info(f"tool_name:{tool_name},tool_input:{tool_input}")
                # 处理工具调用结束
                elif kind == "on_tool_end":
                    tool_output = event.get("data", {}).get("output", "")
                    # 确保tool_output是字符串，处理ToolMessage对象
                    if not isinstance(tool_output, str):
                        if hasattr(tool_output, "content"):
                            tool_output = tool_output.content
                        elif hasattr(tool_output, "__str__"):
                            tool_output = str(tool_output)
                        else:
                            tool_output = ""
                    yield {
                        "type": "tool_end",
                        "tool_output": tool_output
                    }

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }

        # 保存助手回复到memory
        if full_assistant_response:
            await self.memory_manager.add_memory(
                content=full_assistant_response,
                session_id=session_id,
                role="assistant"
            )
        logger.info(f"full_assistant_response:{full_assistant_response}")
    def _build_messages(self,history:list[MemoryItem],new_message:str):
        messages=[]
        for msg in history:
            role=msg.role
            content=msg.content
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        messages.append(HumanMessage(content=new_message))
        return messages