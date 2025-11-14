from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import yaml
import os

router = APIRouter()

class StartTestBody(BaseModel):
    name: str
    config_path: str | None = None
    image_paths: list[str] | None = None

@router.post("/start")
def start_test(body: StartTestBody, request: Request):
    tm = request.app.state.tm

    # 1) Start the test record
    test_id = tm.start_test(body.name)

    # 2) Read YAML if config_path is provided and accessible
    spec = None
    if body.config_path and os.path.exists(body.config_path):
        with open(body.config_path, "r") as f:
            spec = yaml.safe_load(f)
        tm.update_test(test_id, log=f"Loaded YAML spec from {body.config_path}")
    else:
        tm.update_test(test_id, log=f"cli started test with config={body.config_path}, images={body.image_paths}")

    # 3) use `spec` to drive DeviceManager + Device Host calls
    #    e.g., configure firmware flashing, serial streams, logs based on YAML

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
