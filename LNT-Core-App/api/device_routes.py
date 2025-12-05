#define device endpoints
# LNT-Core-App/api/device_routes.py

from fastapi import APIRouter, HTTPException
from core.device_manage import DeviceManager
from pydantic import BaseModel
import os
import requests

router = APIRouter()
device_manage = DeviceManager()

class AddDUTRequest(BaseModel):
    hostname: str
    dut_name: str
    dut_type: str
    cfg_path: str
    usb_port: str

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

@router.post("/dut/add")
def add_dut(request: AddDUTRequest):
    """Add a DUT to a device host"""
    try:
        device_manage.add_dut(
            hostname=request.hostname,
            dut_name=request.dut_name,
            dut_type=request.dut_type,
            cfg_path=request.cfg_path,
            usb_port=request.usb_port
        )
        return {
            "message": f"DUT '{request.dut_name}' added to host '{request.hostname}'",
            "hostname": request.hostname,
            "dut_name": request.dut_name
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding DUT: {str(e)}")

@router.get("/test-connection")
def test_host_connection():
    """Test Core → Host connection using HOST_AGENT_URL from .env"""
    host_agent_url = os.getenv("HOST_AGENT_URL", "http://localhost:8001/").rstrip("/")
    try:
        response = requests.get(f"{host_agent_url}/health", timeout=5)
        response.raise_for_status()
        health_data = response.json()
        
        if health_data.get("status") == "healthy":
            return {
                "status": "success",
                "message": "Core → Host connection working",
                "host_url": host_agent_url,
                "health_response": health_data
            }
        else:
            return {
                "status": "warning",
                "message": "Connection works but unexpected health status",
                "host_url": host_agent_url,
                "health_response": health_data
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to connect to Host Agent",
            "host_url": host_agent_url,
            "error": str(e)
        }
