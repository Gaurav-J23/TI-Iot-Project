from fastapi import APIRouter
from pydantic import BaseModel
from core.test_manage import TestManager

router = APIRouter()
test_manage = TestManager()

class StartTestBody(BaseModel):
    name: str

@router.post("/start")
def start_test(body: StartTestBody):
    test_id = test_manage.start_test(body.name)
    return {"message": f"Started test '{body.name}'", "test_id": test_id}

@router.get("/status")
def get_status():
    return {"tests": test_manage.get_tests()}