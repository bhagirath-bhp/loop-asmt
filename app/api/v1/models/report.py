from pydantic import BaseModel

class ReportGenerationResponse(BaseModel):
    report_id: str

class ReportStatusResponse(BaseModel):
    status: str
    file: Optional[str] = None  # Include file content or path if available
