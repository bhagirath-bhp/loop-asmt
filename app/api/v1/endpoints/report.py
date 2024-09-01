from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.report import generate_report, get_report_status
from api.v1.models.report import ReportGenerationResponse, ReportStatusResponse
from fastapi.responses import FileResponse
import os

router = APIRouter()

# Define response model for trigger_report
class TriggerReportResponse(BaseModel):
    report_id: str

@router.get("/test")
def test_endpoint():
    return {"message": "jaishreeram"}

@router.post("/trigger_report", response_model=TriggerReportResponse)
def trigger_report():
    report_id = generate_report()
    if not report_id:
        raise HTTPException(status_code=500, detail="Failed to generate report")
    return TriggerReportResponse(report_id=report_id)

@router.get("/get_report/{report_id}", response_model=ReportStatusResponse)
def get_report(report_id: str):
    status_info = get_report_status(report_id)
    
    if status_info["status"] == "Unknown":
        raise HTTPException(status_code=404, detail=status_info.get("message", "Report not found"))
    
    if status_info["status"] == "Running":
        return ReportStatusResponse(status="Running")
    
    if status_info["status"] == "Complete":
        file_path = status_info.get("file_path")
        if file_path and os.path.exists(file_path):
            return ReportStatusResponse(status="Complete", file_path=file_path)
        else:
            raise HTTPException(status_code=500, detail="Report file not found")
    
    raise HTTPException(status_code=500, detail="Unexpected error occurred")

@router.get("/download_report/{report_id}")
def download_report(report_id: str):
    status_info = get_report_status(report_id)
    
    if status_info["status"] != "Complete":
        raise HTTPException(status_code=404, detail="Report not found or not complete")
    
    file_path = status_info.get("file_path")
    if file_path and os.path.exists(file_path):
        return FileResponse(path=file_path, media_type='application/csv', filename=os.path.basename(file_path))
    
    raise HTTPException(status_code=500, detail="Report file not found")
