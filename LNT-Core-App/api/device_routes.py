#define device endpoints
from fastapi import APIRouter
from pydantic import BaseModel
from core.device_manage import DeviceManager

router = APIRouter()
device_manage = DeviceManager()

class AddDeviceBody(BaseModel):
    hostname: str

@router.get("/list")
def list_devices():
    return {"hosts": device_manage.get_hosts()}

@router.post("/add")
def add_device(body: AddDeviceBody):
    device_manage.add_host(body.hostname)
    return {"message": f"Device host '{body.hostname}' added successfully."}
