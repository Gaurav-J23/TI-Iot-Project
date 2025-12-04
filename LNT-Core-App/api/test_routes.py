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

    # 1) Load YAML FIRST
    spec = None
    if body.config_path and os.path.exists(body.config_path):
        with open(body.config_path, "r") as f:
            spec = yaml.safe_load(f)

    # 2) Start the test WITH the YAML spec
    test_id = tm.start_test(
        body.name,
        test_config=spec,
        test_yaml_path=body.config_path
    )

    # 3) Log that YAML was loaded (or not)
    if spec is not None:
        tm.update_test(test_id, log=f"Loaded YAML spec from {body.config_path}")
    else:
        tm.update_test(test_id, log=f"Started test with config={body.config_path}, images={body.image_paths}")

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
