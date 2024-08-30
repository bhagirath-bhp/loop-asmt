from fastapi import FastAPI
from api.v1.endpoints.report import router as report_router

app = FastAPI()

# Include routers
app.include_router(report_router, prefix="/api/v1")
