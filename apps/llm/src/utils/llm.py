from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import openai
import requests
from ..config import get_settings

def get_llm(provider: str = "openai", model: str = None):
    """Get configured LLM instance based on provider and model"""
    settings = get_settings()
    
    if provider.lower() == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
        
        if model is None:
            model = "gpt-3.5-turbo-1106"
        
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=model,
            temperature=0.7
        )
    elif provider.lower() == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일에 ANTHROPIC_API_KEY를 추가해주세요.")
        
        if model is None:
            model = "claude-3-haiku-20240307"
        
        return ChatAnthropic(
            api_key=settings.anthropic_api_key,
            model=model,
            temperature=0.7
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

def get_openai_models(api_key: str):
    """OpenAI API에서 사용 가능한 모델 목록 가져오기"""
    try:
        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()
        
        chat_models = []
        for model in models.data:
            if model.id.startswith('gpt-') and 'instruct' not in model.id.lower():
                chat_models.append(model.id)
        
        chat_models.sort(reverse=True)
        return chat_models
    except Exception as e:
        print(f"OpenAI 모델 목록 가져오기 실패: {e}")
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo-preview",
            "gpt-4-1106-preview",
            "gpt-3.5-turbo-1106"
        ]

def get_anthropic_models(api_key: str):
    """Anthropic API에서 사용 가능한 모델 목록 가져오기"""
    try:
        response = requests.get(
            "https://api.anthropic.com/v1/models",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            models = [model["id"] for model in data["data"]]
            models.sort(reverse=True)
            return models
        else:
            raise Exception(f"API 응답 오류: {response.status_code}")
            
    except Exception as e:
        print(f"Anthropic 모델 목록 가져오기 실패: {e}")
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]

def get_available_models():
    """Get list of available models for each provider"""
    settings = get_settings()
    available_models = {}
    
    if settings.openai_api_key:
        available_models["openai"] = get_openai_models(settings.openai_api_key)
    
    if settings.anthropic_api_key:
        available_models["anthropic"] = get_anthropic_models(settings.anthropic_api_key)
    
    return available_models 