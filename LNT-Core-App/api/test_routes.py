#define test endpoints
# LNT-Core-App/api/device_routes.py
from fastapi import APIRouter
from core.test_manage import TestManager

router = APIRouter()
test_manage = TestManager()

@router.post("/start")
def start_test(test_name: str):
    test_id = test_manage.start_test(test_name)
    return {"message": f"Started test '{test_name}'", "test_id": test_id}

@router.get("/status")
def get_status():
    return {"tests": test_manage.get_tests()}
