"""
User Data Upload API Endpoints

사용자 데이터 업로드 (CSV → Candidate 가져오기)
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

router = APIRouter()
logger = structlog.get_logger()


def get_db():
    """Supabase 클라이언트 의존성"""
    from supabase import create_client
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    return create_client(supabase_url, supabase_key)


# === Schemas ===

class PresignRequest(BaseModel):
    """업로드 준비 요청"""
    type: Literal["candidate_csv", "experiment_csv", "doc_pdf"] = "candidate_csv"
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: Optional[str] = "text/csv"
    size_bytes: Optional[int] = None
    user_id: str = Field(..., description="Owner user ID")


class PresignResponse(BaseModel):
    """업로드 준비 응답"""
    upload_id: str
    bucket: str
    key: str
    presigned_url: str
    expires_in: int = 3600


class CommitRequest(BaseModel):
    """업로드 완료 요청"""
    upload_id: str
    user_id: str


class UploadResponse(BaseModel):
    """업로드 정보"""
    id: str
    type: str
    filename: str
    status: str
    created_at: str
    error_message: Optional[str] = None


# === Endpoints ===

@router.post("/presign", response_model=PresignResponse)
async def presign_upload(request: PresignRequest, db=Depends(get_db)):
    """
    업로드 URL 발급 (Pre-sign)
    
    1. uploads 레코드 생성 (status='uploaded')
    2. Supabase Storage presigned URL 발급
    """
    upload_id = str(uuid.uuid4())
    now = datetime.utcnow()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    
    # Storage key 생성
    storage_key = f"users/{request.user_id}/{year}/{month}/{upload_id}/{request.filename}"
    bucket = "user-uploads"
    
    log = logger.bind(upload_id=upload_id, user_id=request.user_id)
    
    try:
        # 1. uploads 레코드 생성
        upload_record = {
            "id": upload_id,
            "owner_user_id": request.user_id,
            "type": request.type,
            "filename": request.filename,
            "storage_bucket": bucket,
            "storage_key": storage_key,
            "mime_type": request.mime_type,
            "size_bytes": request.size_bytes,
            "status": "uploaded"
        }
        
        result = db.table("uploads").insert(upload_record).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create upload record")
        
        log.info("upload_record_created")
        
        # 2. Presigned URL 발급
        # Supabase Storage는 signed URL을 사용
        expires_in = 3600  # 1 hour
        
        try:
            signed_url_result = db.storage.from_(bucket).create_signed_upload_url(storage_key)
            presigned_url = signed_url_result.get("signedURL", "")
            
            if not presigned_url:
                # Fallback: 직접 업로드 URL 구성
                supabase_url = os.getenv("SUPABASE_URL", "")
                presigned_url = f"{supabase_url}/storage/v1/object/{bucket}/{storage_key}"
        except Exception as e:
            log.warning("presign_fallback", error=str(e))
            supabase_url = os.getenv("SUPABASE_URL", "")
            presigned_url = f"{supabase_url}/storage/v1/object/{bucket}/{storage_key}"
        
        return PresignResponse(
            upload_id=upload_id,
            bucket=bucket,
            key=storage_key,
            presigned_url=presigned_url,
            expires_in=expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("presign_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commit")
async def commit_upload(request: CommitRequest, db=Depends(get_db)):
    """
    업로드 완료 알림 (Commit)
    
    1. 업로드 레코드 확인
    2. status='parsing'으로 변경
    3. 파싱 Job enqueue
    """
    log = logger.bind(upload_id=request.upload_id, user_id=request.user_id)
    
    try:
        # 1. 업로드 레코드 확인
        result = db.table("uploads").select("*").eq("id", request.upload_id).eq("owner_user_id", request.user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Upload not found or access denied")
        
        upload = result.data[0]
        
        if upload["status"] != "uploaded":
            raise HTTPException(status_code=400, detail=f"Invalid upload status: {upload['status']}")
        
        # 2. status 변경
        db.table("uploads").update({
            "status": "parsing"
        }).eq("id", request.upload_id).execute()
        
        log.info("upload_committed")
        
        # 3. 파싱 Job enqueue
        try:
            import redis
            import json
            
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            r = redis.from_url(redis_url)
            
            job_data = json.dumps({
                "job": "parse_candidate_csv",
                "upload_id": request.upload_id,
                "user_id": request.user_id,
                "enqueue_time": datetime.utcnow().isoformat()
            })
            
            r.lpush("arq:queue:upload_queue", job_data)
            log.info("parse_job_enqueued")
            
        except Exception as e:
            log.warning("job_enqueue_failed", error=str(e))
            # Job enqueue 실패해도 계속 진행 (수동 실행 가능)
        
        return {
            "status": "parsing",
            "upload_id": request.upload_id,
            "message": "Upload committed. Parsing in progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("commit_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[UploadResponse])
async def list_uploads(
    user_id: str,
    type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db=Depends(get_db)
):
    """
    내 업로드 목록 조회
    """
    try:
        query = db.table("uploads").select("*").eq("owner_user_id", user_id).order("created_at", desc=True)
        
        if type:
            query = query.eq("type", type)
        if status:
            query = query.eq("status", status)
        
        query = query.range(offset, offset + limit - 1)
        result = query.execute()
        
        return [
            UploadResponse(
                id=item["id"],
                type=item["type"],
                filename=item["filename"],
                status=item["status"],
                created_at=item["created_at"],
                error_message=item.get("error_message")
            )
            for item in result.data or []
        ]
        
    except Exception as e:
        logger.error("list_uploads_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(upload_id: str, user_id: str, db=Depends(get_db)):
    """
    업로드 상세 조회
    """
    try:
        result = db.table("uploads").select("*").eq("id", upload_id).eq("owner_user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        item = result.data[0]
        
        return UploadResponse(
            id=item["id"],
            type=item["type"],
            filename=item["filename"],
            status=item["status"],
            created_at=item["created_at"],
            error_message=item.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{upload_id}")
async def delete_upload(upload_id: str, user_id: str, db=Depends(get_db)):
    """
    업로드 삭제
    """
    log = logger.bind(upload_id=upload_id, user_id=user_id)
    
    try:
        # 1. 업로드 확인
        result = db.table("uploads").select("*").eq("id", upload_id).eq("owner_user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        upload = result.data[0]
        
        # 2. Storage에서 파일 삭제
        try:
            db.storage.from_(upload["storage_bucket"]).remove([upload["storage_key"]])
        except Exception as e:
            log.warning("storage_delete_failed", error=str(e))
        
        # 3. 관련 candidates 삭제 (cascade)
        db.table("user_candidates").delete().eq("source_upload_id", upload_id).execute()
        
        # 4. 업로드 레코드 삭제
        db.table("uploads").delete().eq("id", upload_id).execute()
        
        log.info("upload_deleted")
        
        return {"status": "deleted", "upload_id": upload_id}
        
    except HTTPException:
        raise
    except Exception as e:
        log.error("delete_upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
