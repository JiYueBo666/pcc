



def resolve_agent_model(agent_id:str='main'):
    from src.agent.model_config import ModelRef
    from src.config import config
    api_key=config.OPENAI_KEY
    base_url=config.BASE_URL
    temperature=config.TEMPERATURE
    ref=ModelRef(model_id='gpt-4o', api_key=api_key, base_url=base_url)
    return ref