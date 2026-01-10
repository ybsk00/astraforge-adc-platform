"""
AI Utility Functions
"""
import os
import httpx
from typing import List, Optional
import structlog

logger = structlog.get_logger()

EMBEDDING_MODEL = "text-embedding-3-small"

async def get_embedding(text: str) -> Optional[List[float]]:
    """
    OpenAI API를 사용하여 임베딩 생성
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("no_openai_key")
        return None
        
    url = "https://api.openai.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "input": text,
        "model": EMBEDDING_MODEL
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data, timeout=10.0)
            if response.status_code != 200:
                logger.error("openai_api_error", status=response.status_code, body=response.text)
                return None
            
            result = response.json()
            return result["data"][0]["embedding"]
            
    except Exception as e:
        logger.error("embedding_failed", error=str(e))
        return None
