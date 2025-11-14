# actual logic for devices

import yaml
import os
import time
import requests
from utils.ansible_runner import provision_host

INVENTORY_PATH = "ansible/inventory.yml"
HOST_API_PORT = 5001       # adjust to match your Device Host agent
HTTP_TIMEOUT_S = 5         # simple timeout for REST calls

# Map DUT status -> color for GUI
DUT_STATUS_COLOR = {
    "running": "green",
    "idle": "yellow",
    "offline": "red",
}

class DeviceManager:
    def __init__(self):
        self.inventory = self.load_inventory()

    def load_inventory(self):
        """Load inventory from YAML file, creating default structure if missing."""
        if not os.path.exists(INVENTORY_PATH):
            return {"all": {"hosts": {}}}
        with open(INVENTORY_PATH, "r") as f:
            data = yaml.safe_load(f) or {}

        # Normalize to ensure keys exist even if file was partially edited
        if "all" not in data:
            data["all"] = {}
        
        # Handle both structures: all.hosts and all.children.lnt_device_hosts.hosts
        if "hosts" not in data["all"]:
            if "children" in data["all"] and "lnt_device_hosts" in data["all"]["children"]:
                # Extract hosts from nested structure
                nested_hosts = data["all"]["children"]["lnt_device_hosts"].get("hosts", {})
                data["all"]["hosts"] = nested_hosts
            else:
                data["all"]["hosts"] = {}
        
        return data

    # writes current python object back to inventory.yml
    def save_inventory(self):
        os.makedirs(os.path.dirname(INVENTORY_PATH), exist_ok=True)
        with open(INVENTORY_PATH, "w") as f:
            yaml.safe_dump(self.inventory, f, sort_keys=False, default_flow_style=False)

    # QUERIES
    # returns a list of all hosts in inventory
    def list_hosts(self):
        return list(self.inventory["all"]["hosts"].keys())

    # gets all device hosts (full records)
    def get_hosts(self):
        return self.inventory["all"]["hosts"]

    # adds new device host (also provisions via Ansible)
    def add_host(self, hostname, ip_address):
        self.inventory["all"]["hosts"][hostname] = {
            "ansible_host": ip_address,
            "status": "pending",
            "last_seen_epoch": int(time.time()),
            "duts": {
                "count": 0,
                "types": [],
                "items": [],
                "status_counts": {"running": 0, "idle": 0, "offline": 0}
            }
        }
        self.save_inventory()
        
        # Provision via Ansible
        provision_host(hostname, INVENTORY_PATH)
        
        return self.inventory["all"]["hosts"][hostname]

    # removes device host
    def remove_host(self, hostname):
        """Remove a device host from the system. Returns True if removed, False if not found."""
        if hostname in self.inventory["all"]["hosts"]:
            del self.inventory["all"]["hosts"][hostname]
            self.save_inventory()
            return True
        return False

    # refresh a single host's status and DUT list by calling the Device Host REST API
    # expected endpoints on the device host:
    #   GET http://<ip>:<PORT>/api/health -> {"status":"idle"|"busy"}
    #   GET http://<ip>:<PORT>/api/duts   -> {"count":2,"types":["CC26x2","CC13x2"]}
    def refresh_host_status(self, hostname: str):
        host = self.inventory["all"]["hosts"][hostname]
        ip = host["ansible_host"]
        base = f"http://{ip}:{HOST_API_PORT}/api"

        try:
            # Pull host health (busy/idle) and DUT details from the agent.
            health = requests.get(f"{base}/health", timeout=HTTP_TIMEOUT_S).json()
            duts_resp = requests.get(f"{base}/duts", timeout=HTTP_TIMEOUT_S).json()

            # update host status
            host["status"] = health.get("status", "idle")
            host["last_seen_epoch"] = int(time.time())

            items = duts_resp.get("items")

            if isinstance(items, list):
                # normalize each item and attach color
                normalized = []
                status_counts = {"running": 0, "idle": 0, "offline": 0}
                types = []

                # Try several common keys to derive a unique DUT identifier; fallback to auto-number.
                for it in items:
                    dut_id = str(it.get("id") or it.get("serial") or it.get("name") or f"dut-{len(normalized) + 1}")
                    dut_type = str(it.get("type") or "")
                    status = str(it.get("status") or "idle").lower()
                    if status not in ("running", "idle", "offline"):
                        status = "idle"
                    color = DUT_STATUS_COLOR[status]
                    normalized.append({
                        "id": dut_id,
                        "type": dut_type,
                        "status": status,
                        "color": color,
                    })
                    if dut_type:
                        types.append(dut_type)
                    status_counts[status] += 1

                # Persist a full DUT block the GUI can render without more processing.
                host["duts"] = {
                    "count": len(normalized),
                    "types": sorted(set(types)),
                    "items": normalized,
                    "status_counts": status_counts,
                }

            else:
                # Legacy/simple shape: {"count": 2, "types": ["CC26x2","CC13x2"]}
                count = int(duts_resp.get("count", 0))
                types = list(duts_resp.get("types", []))

                # Without per-DUT info, assume all idle so GUI shows yellow
                items = [{
                    "id": f"dut-{i + 1}",
                    "type": (types[i] if i < len(types) else ""),
                    "status": "idle",
                    "color": DUT_STATUS_COLOR["idle"],
                } for i in range(count)]

                host["duts"] = {
                    "count": count,
                    "types": types,
                    "items": items,
                    "status_counts": {
                        "running": 0,
                        "idle": count,
                        "offline": 0
                    },
                }

            self.save_inventory()
            return host
        except requests.exceptions.RequestException as e:
            # Mark host as disconnected if API call fails
            host["status"] = "disconnected"
            host["last_seen_epoch"] = int(time.time())
            self.save_inventory()
            return host

    # refresh every host, return a dict of hostname -> record
    def refresh_all_statuses(self):
        return {h: self.refresh_host_status(h) for h in self.list_hosts()}

    # tiny stats block GUI/CLI can show
    def inventory_stats(self):
        hosts = self.inventory["all"]["hosts"]
        status_counts = {"idle": 0, "busy": 0, "disconnected": 0, "pending": 0, "provisioning": 0, "error": 0}
        total_duts = 0
        for h in hosts.values():
            s = h.get("status", "idle")
            status_counts[s] = status_counts.get(s, 0) + 1
            total_duts += int(h.get("duts", {}).get("count", 0))
        return {
            "host_count": len(hosts),
            "status_counts": status_counts,
            "total_duts": total_duts,
        }
