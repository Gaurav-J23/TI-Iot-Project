from fastapi import APIRouter, Body, Request
from pydantic import BaseModel, IPvAnyAddress

router = APIRouter()

class AddDeviceReq(BaseModel):
    hostname: str
    ip: IPvAnyAddress

@router.get("")
def list_devices(request: Request):
    """List all device hosts + basic stats for the dashboard / CLI."""
    dm = request.app.state.dm
    return {
        "hosts": dm.get_hosts(),        # {hostname: {...}}
        "stats": dm.inventory_stats(),  # {host_count, status_counts, ...}
    }

@router.post("")
def add_device(payload: AddDeviceReq, request: Request):
    dm = request.app.state.dm
    record = dm.add_host(payload.hostname, str(payload.ip))
    return {"message": f"Device host '{payload.hostname}' added.", "record": record}

@router.post("/{hostname}/refresh")
def refresh_device(hostname: str, request: Request):
    dm = request.app.state.dm
    record = dm.refresh_host_status(hostname)
    return {"hostname": hostname, "record": record}

@router.delete("/{hostname}")
def delete_device(hostname: str, request: Request):
    dm = request.app.state.dm
    dm.remove_hosts(hostname)
    return {"message": f"Device host '{hostname}' removed."}
