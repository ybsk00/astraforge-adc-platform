"""
CSV Candidate Parsing Job

업로드된 CSV 파일을 파싱하여 후보 데이터로 변환
"""
import os
import io
import csv
from typing import Dict, Any, List, Optional
import structlog
from supabase import create_client

logger = structlog.get_logger()

# CSV 컬럼 매핑 (기획안 기준)
REQUIRED_COLUMNS = ["name"]
FEATURE_COLUMNS = ["DAR", "LogP", "AggRisk", "H_patch", "CLV", "INT"]


def get_db():
    """Supabase 클라이언트"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Database not configured")
    
    return create_client(supabase_url, supabase_key)


async def parse_candidate_csv_job(ctx: Dict[str, Any], upload_id: str, user_id: str):
    """
    CSV 파싱 Job
    
    1. uploads 레코드 조회
    2. Storage에서 파일 다운로드
    3. CSV 파싱 및 검증
    4. user_candidates, candidate_inputs 생성
    5. uploads.status 업데이트
    """
    log = logger.bind(upload_id=upload_id, user_id=user_id)
    db = get_db()
    
    try:
        log.info("parse_job_started")
        
        # 1. 업로드 레코드 조회
        result = db.table("uploads").select("*").eq("id", upload_id).eq("owner_user_id", user_id).execute()
        
        if not result.data:
            log.error("upload_not_found")
            return {"status": "error", "message": "Upload not found"}
        
        upload = result.data[0]
        
        # 2. Storage에서 파일 다운로드
        try:
            file_data = db.storage.from_(upload["storage_bucket"]).download(upload["storage_key"])
        except Exception as e:
            log.error("file_download_failed", error=str(e))
            await update_upload_status(db, upload_id, "failed", f"파일 다운로드 실패: {str(e)}")
            return {"status": "error", "message": str(e)}
        
        # 3. CSV 파싱
        try:
            # 바이트를 문자열로 변환
            content = file_data.decode('utf-8-sig')  # BOM 처리
            reader = csv.DictReader(io.StringIO(content))
            
            # 컬럼 검증
            fieldnames = reader.fieldnames or []
            missing_columns = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
            
            if missing_columns:
                error_msg = f"필수 컬럼 누락: {', '.join(missing_columns)}"
                log.error("validation_failed", error=error_msg)
                await update_upload_status(db, upload_id, "failed", error_msg)
                return {"status": "error", "message": error_msg}
            
            rows = list(reader)
            
        except Exception as e:
            log.error("csv_parse_failed", error=str(e))
            await update_upload_status(db, upload_id, "failed", f"CSV 파싱 실패: {str(e)}")
            return {"status": "error", "message": str(e)}
        
        # 4. Candidates 생성
        created_count = 0
        error_rows = []
        
        for idx, row in enumerate(rows):
            try:
                # 이름 검증
                name = row.get("name", "").strip()
                if not name:
                    error_rows.append({"row": idx + 2, "error": "이름 누락"})
                    continue
                
                # Features 추출
                features = {}
                for col in FEATURE_COLUMNS:
                    if col in row and row[col]:
                        try:
                            features[col] = float(row[col])
                        except ValueError:
                            features[col] = None
                
                # Candidate 생성
                candidate_result = db.table("user_candidates").insert({
                    "owner_user_id": user_id,
                    "name": name,
                    "metadata": {k: v for k, v in row.items() if k not in FEATURE_COLUMNS and k != "name"},
                    "features": features,
                    "source_upload_id": upload_id
                }).execute()
                
                if candidate_result.data:
                    candidate_id = candidate_result.data[0]["id"]
                    
                    # Candidate Input (원본 행) 저장
                    db.table("candidate_inputs").insert({
                        "candidate_id": candidate_id,
                        "owner_user_id": user_id,
                        "raw_row": row,
                        "row_index": idx
                    }).execute()
                    
                    created_count += 1
                    
            except Exception as e:
                log.warning("row_process_failed", row_index=idx, error=str(e))
                error_rows.append({"row": idx + 2, "error": str(e)})
        
        # 5. 결과 업데이트
        if created_count > 0:
            status = "parsed"
            error_message = None
            if error_rows:
                error_message = f"{created_count}건 생성, {len(error_rows)}건 오류"
        else:
            status = "failed"
            error_message = "유효한 데이터가 없습니다"
        
        await update_upload_status(db, upload_id, status, error_message)
        
        log.info("parse_job_completed", created=created_count, errors=len(error_rows))
        
        return {
            "status": status,
            "created_count": created_count,
            "error_count": len(error_rows),
            "errors": error_rows[:10]  # 최대 10개만 반환
        }
        
    except Exception as e:
        log.error("parse_job_failed", error=str(e))
        await update_upload_status(db, upload_id, "failed", str(e))
        return {"status": "error", "message": str(e)}


async def update_upload_status(db, upload_id: str, status: str, error_message: Optional[str] = None):
    """업로드 상태 업데이트"""
    update_data = {"status": status}
    if error_message:
        update_data["error_message"] = error_message
    
    db.table("uploads").update(update_data).eq("id", upload_id).execute()
