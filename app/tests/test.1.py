from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_trigger_report():
    response = client.post("/trigger_report")
    assert response.status_code == 200
    assert "report_id" in response.json()

def test_get_report():
    response = client.get("/get_report/some_report_id")
    assert response.status_code == 200
