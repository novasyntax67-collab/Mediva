from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Healthcare Platform API"
    API_V1_STR: str = "/api/v1"
    ENABLE_DEV_AUTH: bool = False
    
    # Supabase config
    SUPABASE_URL: str = "https://your-supabase-project.supabase.co"
    SUPABASE_ANON_KEY: str = "anon-key"
    SUPABASE_SERVICE_ROLE_KEY: str = "service-role-key"
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # DB config
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/healthcare"
    
    # Redis & Queue config
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Livekit
    LIVEKIT_API_KEY: str = "devkey"
    LIVEKIT_API_SECRET: str = "devkey-secret-long-secure-32-characters-minimum"
    LIVEKIT_URL: str = "http://localhost:7880"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
