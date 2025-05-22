from langchain_openai import ChatOpenAI
from ..config import get_settings

def get_llm():
    """Get configured LLM instance"""
    settings = get_settings()
    
    return ChatOpenAI(
        api_key=settings.openai_api_key,
        model="gpt-3.5-turbo-1106",
        temperature=0.7
    ) 