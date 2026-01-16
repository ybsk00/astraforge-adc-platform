"""
Global Exception Handlers
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Union
import uuid
import structlog

logger = structlog.get_logger()


async def global_exception_handler(
    request: Request, exc: Union[HTTPException, Exception]
):
    """
    모든 예외를 표준 에러 포맷으로 변환
    """
    trace_id = str(uuid.uuid4())

    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        error_code = "HTTP_ERROR"
        message = exc.detail
        # Custom headers if any
        headers = exc.headers
    else:
        status_code = 500
        error_code = "INTERNAL_SERVER_ERROR"
        message = str(exc) if str(exc) else "An unexpected error occurred."
        headers = None

        # Log unexpected errors
        logger.error(
            "unhandled_exception",
            error=str(exc),
            trace_id=trace_id,
            path=request.url.path,
            method=request.method,
        )

    return JSONResponse(
        status_code=status_code,
        content={"error_code": error_code, "message": message, "trace_id": trace_id},
        headers=headers,
    )
