#define device endpoints
# LNT-Core-App/api/device_routes.py

from fastapi import APIRouter
from core.device_manage import DeviceManager

router = APIRouter()
device_manage = DeviceManager()

@router.get("/list")
def list_devices():
    return {"hosts": device_manage.get_hosts()}

@router.post("/add")
def add_device(hostname: str):
    device_manage.add_host(hostname)
    return {"message": f"Device host '{hostname}' added successfully."}
