from fastapi import FastAPI
from api.v1.endpoints.report import router as report_router

app = FastAPI()

app.include_router(report_router)
