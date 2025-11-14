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
def add_device(hostname: str, ip_address: str):
    host = device_manage.add_host(hostname, ip_address)
    return {"message": f"Device host '{hostname}' added successfully.", "host": host}

@router.post("/remove")
def remove_device(hostname: str):
    result = device_manage.remove_host(hostname)
    if result:
        return {"message": f"Device host '{hostname}' removed successfully."}
    return {"error": f"Device host '{hostname}' not found."}

@router.get("/refresh/{hostname}")
def refresh_host(hostname: str):
    host = device_manage.refresh_host_status(hostname)
    return {"host": host}

@router.get("/refresh-all")
def refresh_all_hosts():
    hosts = device_manage.refresh_all_statuses()
    return {"hosts": hosts}

@router.get("/stats")
def get_stats():
    return device_manage.inventory_stats()
