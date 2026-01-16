"""
Literature Indexing Job
문헌 텍스트 청킹 및 임베딩 생성
"""

import os
import httpx
from typing import Dict, Any, List
import structlog
from supabase import create_client

logger = structlog.get_logger()

# === Settings ===
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "text-embedding-3-small"


def get_db():
    """Supabase 클라이언트"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Database not configured")
    return create_client(supabase_url, supabase_key)


async def get_embedding(text: str, api_key: str) -> List[float]:
    """OpenAI API를 사용하여 임베딩 생성"""
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {"input": text, "model": EMBEDDING_MODEL}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data, timeout=10.0)
        if response.status_code != 200:
            raise Exception(f"OpenAI API Error: {response.text}")

        result = response.json()
        return result["data"][0]["embedding"]


def split_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """간단한 텍스트 청킹 (Character based)"""
    if not text:
        return []

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


async def index_literature_job(ctx: Dict[str, Any], document_id: str):
    """
    문헌 인덱싱 Job

    1. literature_documents 조회
    2. 텍스트 청킹
    3. 임베딩 생성 (OpenAI)
    4. literature_chunks 저장
    """
    log = logger.bind(document_id=document_id)
    db = get_db()
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        log.info("indexing_started")

        # 1. 문서 조회
        result = (
            db.table("literature_documents").select("*").eq("id", document_id).execute()
        )
        if not result.data:
            log.error("document_not_found")
            return {"status": "error", "message": "Document not found"}

        doc = result.data[0]

        # 텍스트 결합 (Title + Abstract + Body if available)
        full_text = f"{doc.get('title', '')}\n\n{doc.get('abstract', '')}"
        # TODO: Body text if stored separately

        if not full_text.strip():
            log.warning("empty_text_skipped")
            return {"status": "skipped", "message": "Empty text"}

        # 2. 청킹
        chunks = split_text(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
        log.info("text_chunked", count=len(chunks))

        # 3. 임베딩 및 저장
        chunk_inserts = []

        for idx, chunk_text in enumerate(chunks):
            embedding = None
            embedding_status = "pending"

            if api_key:
                try:
                    embedding = await get_embedding(chunk_text, api_key)
                    embedding_status = "completed"
                except Exception as e:
                    log.error("embedding_failed", chunk_index=idx, error=str(e))
                    embedding_status = "failed"
            else:
                log.warning("no_openai_key_skipping_embedding")
                embedding_status = "pending"  # Key 없으면 pending으로 둠

            chunk_inserts.append(
                {
                    "document_id": document_id,
                    "chunk_index": idx,
                    "content": chunk_text,
                    "token_count": len(chunk_text) // 4,  # Rough estimate
                    "embedding": embedding,  # vector type handles list[float]
                    "embedding_status": embedding_status,
                }
            )

        # 4. 저장 (기존 청크 삭제 후 재생성)
        db.table("literature_chunks").delete().eq("document_id", document_id).execute()

        if chunk_inserts:
            db.table("literature_chunks").insert(chunk_inserts).execute()

        log.info("indexing_completed", chunks=len(chunk_inserts))
        return {"status": "completed", "chunks": len(chunk_inserts)}

    except Exception as e:
        log.error("indexing_failed", error=str(e))
        return {"status": "error", "message": str(e)}
