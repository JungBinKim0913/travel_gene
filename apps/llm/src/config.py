from pydantic_settings import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    google_calendar_api_key: str = os.getenv("GOOGLE_CALENDAR_API_KEY")
    kakao_api_key: str = os.getenv("KAKAO_API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 