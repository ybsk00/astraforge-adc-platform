"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path


# 프로젝트 루트 경로 찾기
def find_env_file():
    """프로젝트 루트의 .env 파일 찾기"""
    current = Path(__file__).resolve()
    # services/engine/app/core/config.py -> 프로젝트 루트
    for _ in range(5):
        current = current.parent
        env_path = current / ".env"
        if env_path.exists():
            return str(env_path)
    return ".env"  # 기본값


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # Redis (Arq)
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM
    GEMINI_API_KEY: str = ""
    
    # Embedding
    OPENAI_API_KEY: str = ""
    
    # PubMed
    NCBI_API_KEY: str = ""
    NCBI_EMAIL: str = ""
    NCBI_TOOL: str = "adc_platform"
    
    # CORS - 쉼표로 구분된 문자열로 받음
    CORS_ORIGINS: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """CORS 오리진 리스트 반환"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = find_env_file()
        case_sensitive = True


settings = Settings()

# 설정 검증 로그
if settings.DEBUG:
    import structlog
    logger = structlog.get_logger()
    if not settings.SUPABASE_URL:
        logger.warning("SUPABASE_URL is not set")
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.warning("SUPABASE_SERVICE_ROLE_KEY is not set")
