"""
Security Utilities
"""
from fastapi import HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
import os
import re

ADMIN_API_KEY_NAME = "X-Admin-Key"
admin_api_key_header = APIKeyHeader(name=ADMIN_API_KEY_NAME, auto_error=False)

def get_admin_key():
    """Admin Key from env"""
    return os.getenv("ADMIN_API_KEY", "admin-secret-key")

async def require_admin(
    api_key_header: str = Security(admin_api_key_header),
):
    """
    관리자 권한 확인
    1. X-Admin-Key 헤더 확인
    2. (TODO) Supabase User Role 확인
    """
    if api_key_header == get_admin_key():
        return True
    
    # TODO: Check Supabase JWT for admin role
    # For now, simple key check or fail
    raise HTTPException(
        status_code=403,
        detail="Admin privileges required"
    )

# Masking Patterns
SENSITIVE_PATTERNS = {
    "api_key": r"(?i)(api_key|apikey|key|token|secret|password|credential)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-\.]+)[\"']?",
    "email": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
    "phone": r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4})"
}

def mask_sensitive_data(text: str) -> str:
    """민감 정보 마스킹"""
    if not text:
        return text
        
    masked = text
    for name, pattern in SENSITIVE_PATTERNS.items():
        masked = re.sub(pattern, lambda m: m.group(0).replace(m.group(2) if len(m.groups()) > 1 else m.group(1), "***"), masked)
    
    return masked

def mask_log_entry(entry: dict) -> dict:
    """로그 엔트리 마스킹"""
    new_entry = entry.copy()
    
    # Message masking
    if "message" in new_entry and isinstance(new_entry["message"], str):
        new_entry["message"] = mask_sensitive_data(new_entry["message"])
        
    # Meta/Details masking
    if "meta" in new_entry and isinstance(new_entry["meta"], dict):
        for k, v in new_entry["meta"].items():
            if isinstance(v, str):
                new_entry["meta"][k] = mask_sensitive_data(v)
                
    if "metadata" in new_entry and isinstance(new_entry["metadata"], dict):
        for k, v in new_entry["metadata"].items():
            if isinstance(v, str):
                new_entry["metadata"][k] = mask_sensitive_data(v)
                
    return new_entry
