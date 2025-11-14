from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()

class StartTestBody(BaseModel):
    name: str
    config_path: str | None = None
    image_paths: list[str] | None = None

@router.post("/start")
def start_test(body: StartTestBody, request: Request):
    tm = request.app.state.tm
    test_id = tm.start_test(body.name)

    # optional: log the config/image info so logs show something meaningful
    meta = f"config={body.config_path}, images={body.image_paths}"
    tm.update_test(test_id, log=f"cli started test with {meta}")

    return {"message": f"Started test '{body.name}'", "test_id": test_id}

@router.post("/{test_id}/stop")
def stop_test(test_id: int, request: Request):
    tm = request.app.state.tm
    updated = tm.update_test(test_id, status="cancelled", log="Stopped by CLI")
    if not updated:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"message": "Test stopped", "record": updated}

@router.get("/status")
def get_status(request: Request):
    tm = request.app.state.tm
    return {"tests": tm.get_tests()}

@router.get("/{test_id}/logs")
def get_logs(test_id: int, request: Request):
    tm = request.app.state.tm
    test = tm.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"logs": test.get("logs", [])}
