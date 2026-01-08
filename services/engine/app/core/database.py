"""
Supabase Database Client
"""
from supabase import create_client, Client
from app.core.config import settings


def get_supabase_client() -> Client:
    """Supabase 클라이언트 생성"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )


# 싱글톤 클라이언트
_supabase_client: Client | None = None


def get_db() -> Client:
    """Supabase 클라이언트 싱글톤"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client
