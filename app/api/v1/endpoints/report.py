from fastapi import APIRouter, HTTPException
from typing import Dict
from pydantic import BaseModel
from services.report import generate_report, get_report_status

router = APIRouter()

class TriggerReportResponse(BaseModel):
    report_id: str

@router.post("/trigger_report", response_model=TriggerReportResponse)
def trigger_report():
    report_id = generate_report()
    return TriggerReportResponse(report_id=report_id)

@router.get("/get_report/{report_id}")
def get_report(report_id: str):
    status, file_content = get_report_status(report_id)
    if status == "Running":
        return {"status": "Running"}
    elif status == "Complete":
        return {"status": "Complete", "file": file_content}
    else:
        raise HTTPException(status_code=404, detail="Report not found")
