"""
PubMed Chunk → Embed Pipeline E2E Verification

이 스크립트는 전체 파이프라인을 검증합니다:
1. PubMed에서 문헌 수집
2. literature_documents에 저장
3. Chunk 생성
4. Embedding 생성

실행: python tests/e2e/pubmed_embed_pipeline.py
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded .env from {env_path}")
    else:
        print(f"⚠️ No .env file found at {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

try:
    from supabase import create_client
except ImportError:
    print("Error: supabase not installed. Run: pip install supabase")
    sys.exit(1)


def get_supabase():
    """Supabase 클라이언트 생성"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables required")
        print("Create a .env file in the project root with these variables.")
        sys.exit(1)
    
    return create_client(url, key)


def check_literature_documents(db, limit: int = 100) -> dict:
    """literature_documents 테이블 확인"""
    result = db.table("literature_documents").select("id, pmid, title").order("created_at", desc=True).limit(limit).execute()
    
    return {
        "count": len(result.data),
        "items": result.data[:5],
    }


def check_literature_chunks(db, limit: int = 100) -> dict:
    """literature_chunks 테이블 확인"""
    result = db.table("literature_chunks").select("id, document_id, content, embedding").order("created_at", desc=True).limit(limit).execute()
    
    with_embedding = sum(1 for c in result.data if c.get("embedding") is not None)
    without_embedding = sum(1 for c in result.data if c.get("embedding") is None)
    
    return {
        "total_chunks": len(result.data),
        "with_embedding": with_embedding,
        "without_embedding": without_embedding,
        "embedding_rate": round(with_embedding / len(result.data) * 100, 1) if result.data else 0,
    }


def check_chunk_coverage(db) -> dict:
    """문서별 청크 커버리지 확인"""
    docs = db.table("literature_documents").select("id").order("created_at", desc=True).limit(100).execute()
    
    if not docs.data:
        return {"coverage": 0, "docs_with_chunks": 0, "total_docs": 0}
    
    doc_ids = [d["id"] for d in docs.data]
    chunks = db.table("literature_chunks").select("document_id").in_("document_id", doc_ids).execute()
    unique_doc_ids = set(c["document_id"] for c in chunks.data)
    
    return {
        "total_docs": len(doc_ids),
        "docs_with_chunks": len(unique_doc_ids),
        "coverage": round(len(unique_doc_ids) / len(doc_ids) * 100, 1) if doc_ids else 0,
    }


def check_embedding_quality(db, sample_size: int = 5) -> dict:
    """임베딩 품질 샘플 확인"""
    result = db.table("literature_chunks").select("id, content, embedding_model").filter("embedding", "neq", None).order("created_at", desc=True).limit(sample_size).execute()
    
    samples = []
    for chunk in result.data:
        samples.append({
            "id": chunk["id"],
            "content_preview": chunk.get("content", "")[:100] + "...",
            "model": chunk.get("embedding_model", "unknown"),
        })
    
    return {"sample_count": len(samples), "samples": samples}


def run_verification():
    """전체 파이프라인 검증 실행"""
    print("=" * 60)
    print("PubMed Chunk → Embed Pipeline Verification")
    print("=" * 60)
    print(f"Time: {datetime.now(timezone.utc).isoformat()}")
    print()
    
    db = get_supabase()
    
    # 1. Literature Documents 확인
    print("📚 1. Literature Documents")
    print("-" * 40)
    docs = check_literature_documents(db)
    print(f"   Total Documents (recent 100): {docs['count']}")
    if docs['items']:
        print(f"   Sample: {docs['items'][0].get('title', 'N/A')[:50]}...")
    print()
    
    # 2. Literature Chunks 확인
    print("📄 2. Literature Chunks")
    print("-" * 40)
    chunks = check_literature_chunks(db)
    print(f"   Total Chunks: {chunks['total_chunks']}")
    print(f"   With Embedding: {chunks['with_embedding']}")
    print(f"   Without Embedding: {chunks['without_embedding']}")
    print(f"   Embedding Rate: {chunks['embedding_rate']}%")
    print()
    
    # 3. Coverage 확인
    print("📊 3. Document → Chunk Coverage")
    print("-" * 40)
    coverage = check_chunk_coverage(db)
    print(f"   Total Docs Checked: {coverage['total_docs']}")
    print(f"   Docs with Chunks: {coverage['docs_with_chunks']}")
    print(f"   Coverage: {coverage['coverage']}%")
    print()
    
    # 4. Embedding 품질 샘플
    print("🧬 4. Embedding Quality Samples")
    print("-" * 40)
    quality = check_embedding_quality(db)
    for sample in quality['samples']:
        print(f"   - Model: {sample['model']}")
        print(f"     Content: {sample['content_preview']}")
    print()
    
    # 5. 결과 요약
    print("=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    success = True
    
    if docs['count'] < 10:
        print("❌ FAIL: Not enough documents (< 10)")
        success = False
    else:
        print(f"✅ PASS: Documents = {docs['count']}")
    
    if chunks['total_chunks'] < 10:
        print("❌ FAIL: Not enough chunks (< 10)")
        success = False
    else:
        print(f"✅ PASS: Chunks = {chunks['total_chunks']}")
    
    if chunks['embedding_rate'] < 95.0:
        print(f"⚠️ WARNING: Embedding rate {chunks['embedding_rate']}% < 95%")
        if chunks['embedding_rate'] < 50.0:
            success = False
    else:
        print(f"✅ PASS: Embedding rate = {chunks['embedding_rate']}%")
    
    if coverage['coverage'] < 80.0:
        print(f"⚠️ WARNING: Coverage {coverage['coverage']}% < 80%")
    else:
        print(f"✅ PASS: Coverage = {coverage['coverage']}%")
    
    print()
    print("=" * 60)
    if success:
        print("🎉 OVERALL: PASS")
    else:
        print("💥 OVERALL: FAIL (check logs above)")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    run_verification()
