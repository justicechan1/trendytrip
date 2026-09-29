import uuid
import logging
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette import status
from fastapi.exceptions import RequestValidationError
from app.schemas.common import ErrorResponse
from app.core.error_codes import ErrorCode

log = logging.getLogger("uvicorn.error")

# --- 애플리케이션 표준 예외들 ---
class AppError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str):
        super().__init__(status_code=status_code, detail={
            "status": "error",
            "error_code": error_code,
            "message": message,
        })

class BadRequestError(AppError):
    def __init__(self, message="잘못된 요청입니다."):
        super().__init__(status.HTTP_400_BAD_REQUEST, ErrorCode.INVALID_INPUT, message)

class NotFoundError(AppError):
    def __init__(self, message="리소스를 찾을 수 없습니다."):
        super().__init__(status.HTTP_404_NOT_FOUND, ErrorCode.NOT_FOUND, message)

class DeprecatedError(AppError):
    def __init__(self, message="더 이상 사용되지 않는 엔드포인트입니다."):
        super().__init__(status.HTTP_410_GONE, ErrorCode.DEPRECATED_ENDPOINT, message)

# --- trace_id 유틸 ---
def _ensure_trace_id(request: Request) -> str:
    return request.headers.get("x-request-id") or request.headers.get("x-trace-id") or str(uuid.uuid4())

# --- 핸들러: AppError -> JSON ---
async def app_error_handler(request: Request, exc: AppError):
    trace_id = _ensure_trace_id(request)
    payload = exc.detail.copy()
    payload["trace_id"] = trace_id
    log.warning(f"[{trace_id}] {payload['error_code']} - {payload['message']}")
    return JSONResponse(status_code=exc.status_code, content=payload)

# --- 핸들러: FastAPI 유효성 검증(422) ---
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    trace_id = _ensure_trace_id(request)
    items = []
    for e in exc.errors():
        loc = ".".join(str(x) for x in e.get("loc", []))
        items.append({
            "loc": loc,
            "msg": e.get("msg", ""),
            "type": e.get("type", "")
        })
    payload = ErrorResponse(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="요청 본문/쿼리의 유효성 검증에 실패했습니다.",
        trace_id=trace_id,
        errors=items
    ).model_dump()
    log.info(f"[{trace_id}] VALIDATION_ERROR - {items}")
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)

# --- 핸들러: 일반 HTTPException (404 라우팅 포함) ---
async def http_exception_handler(request: Request, exc: HTTPException):
    trace_id = _ensure_trace_id(request)
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    payload = ErrorResponse(
        error_code=ErrorCode.HTTP_EXCEPTION,
        message=message,
        trace_id=trace_id
    ).model_dump()
    # NotFound 등 라우팅 오류도 여기서 통일
    log.warning(f"[{trace_id}] HTTP_EXCEPTION {exc.status_code} - {message}")
    return JSONResponse(status_code=exc.status_code, content=payload)

# --- 핸들러: 완전 예기치 못한 예외(500) ---
async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = _ensure_trace_id(request)
    payload = ErrorResponse(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="서버 내부 오류가 발생했습니다.",
        trace_id=trace_id
    ).model_dump()
    log.exception(f"[{trace_id}] INTERNAL_ERROR: {exc}")
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
