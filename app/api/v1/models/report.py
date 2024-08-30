from pydantic import BaseModel
from typing import Optional

class ReportGenerationResponse(BaseModel):
    report_id: str

class ReportStatusResponse(BaseModel):
    status: str
    file_path: Optional[str] = None  # Path to the report file, if available
    message: Optional[str] = None    # Optional message for error handling
