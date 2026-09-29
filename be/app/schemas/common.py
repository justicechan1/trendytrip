from pydantic import BaseModel
from typing import List, Optional, Literal, TypedDict

class ValidationItem(TypedDict):
    loc: str
    msg: str
    type: str

class ErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error_code: str
    message: str
    trace_id: Optional[str] = None
    errors: Optional[List[ValidationItem]] = None
