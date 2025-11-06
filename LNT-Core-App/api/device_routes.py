#define device endpoints
from fastapi import APIRouter, Body
from pydantic import BaseModel, IPvAnyAddress
from core.device_manage import DeviceManager

router = APIRouter()
dm = DeviceManager()


class AddDeviceReq(BaseModel):
    hostname: str
    ip: IPvAnyAddress

@router.get("")
def list_devices():
    """List all device hosts + basic stats for the dashboard."""
    return {
        "hosts": dm.get_hosts(),        # {hostname: {...}}
        "stats": dm.inventory_stats()   # {host_count, status_counts, ...}
    }

@router.post("")
def add_device(payload: AddDeviceReq):
    #add or provision host
    dm.add_host(payload.hostname, str(payload.ip))
    return {"message": f"Device host '{payload.hostname}' added."}

@router.post("/{hostname}/refresh")
def refresh_device(hostname: str):
    #query device host rest api to status update DUT
    record = dm.refresh_host_status(hostname)
    return {"hostname": hostname, "record": record}

@router.delete("/{hostname}")
def delete_device(hostname: str):
    #remove device host from inventory
    dm.remove_hosts(hostname)
    return {"message": f"Device host '{hostname}' removed."}

