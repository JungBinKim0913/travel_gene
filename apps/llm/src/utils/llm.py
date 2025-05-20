from langchain_openai import ChatOpenAI
from ..config import get_settings

def get_llm():
    """Get configured LLM instance"""
    settings = get_settings()
    
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-3.5-turbo",  # 또는 다른 적절한 모델
        temperature=0.7
    ) 