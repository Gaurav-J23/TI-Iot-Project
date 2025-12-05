# actual logic for devices

import yaml
import os
import time
import requests
from dotenv import load_dotenv
from utils.ansible_runner import provision_host

# Load environment variables
load_dotenv()

INVENTORY_PATH = "ansible/inventory.yml"
HTTP_TIMEOUT_S = 5         # simple timeout for REST calls

DEFAULT_OPENOCD_CFG = "/etc/openocd/boards/cc26x2.cfg"

def get_host_agent_url():
    """Get Host Agent URL from environment variable, fallback to default"""
    return os.getenv("HOST_AGENT_URL", "http://localhost:8001/").rstrip("/")

# Map DUT status -> color for GUI
DUT_STATUS_COLOR = {
    "running": "green",
    "idle": "yellow",
    "offline": "red",
}


class DeviceManager:
    def __init__(self):
        self.inventory = self.load_inventory()


    #load inventory
    def load_inventory(self):
        """Load inventory from YAML file, ensuring OpenOCD config is present per host."""
        if not os.path.exists(INVENTORY_PATH):
            return {"all": {"hosts": {}}}

        with open(INVENTORY_PATH, "r") as f:
            data = yaml.safe_load(f) or {}

        # Ensure correct top-level structure
        data.setdefault("all", {})
        data["all"].setdefault("hosts", {})

        # 🔵 NEW: inject OpenOCD cfg if missing
        for host, info in data["all"]["hosts"].items():
            if "openocd_cfg" not in info:
                info["openocd_cfg"] = DEFAULT_OPENOCD_CFG

        return data


    #save inventory
    def save_inventory(self):
        os.makedirs(os.path.dirname(INVENTORY_PATH), exist_ok=True)
        with open(INVENTORY_PATH, "w") as f:
            yaml.safe_dump(self.inventory, f, sort_keys=False, default_flow_style=False)


    #queries
    def list_hosts(self):
        return list(self.inventory["all"]["hosts"].keys())

    def get_hosts(self):
        return self.inventory["all"]["hosts"]


    #add host w openocd config
    def add_host(self, hostname, ip_address):
        """Register a new LNT Device Host (Raspberry Pi) into the inventory."""

        self.inventory.setdefault("all", {}).setdefault("hosts", {})

        self.inventory["all"]["hosts"][hostname] = {
            "ansible_host": ip_address,

            # Core App uses this to call the Host Agent REST API
            "host_agent_url": f"http://{ip_address}:8001",

            # tracking
            "status": "pending",
            "last_seen_epoch": int(time.time()),

            "openocd_cfg": DEFAULT_OPENOCD_CFG,
            # empty DUT list for now
            "dut_list": {}


        }

        self.save_inventory()

    #add dut
    def add_dut(self, hostname, dut_name, dut_type, cfg_path, usb_port):
        """
        Add a DUT under a specific device host.
        Each DUT gets its own OpenOCD config and USB mapping.
        """

        hosts = self.inventory.get("all", {}).get("hosts", {})
        if hostname not in hosts:
            raise ValueError(f"Host '{hostname}' not found in inventory.")

        # Ensure dut_list exists
        host_entry = hosts[hostname]
        host_entry.setdefault("dut_list", {})

        # Create the DUT entry
        host_entry["dut_list"][dut_name] = {
            "type": dut_type,
            "config": cfg_path,  # the OpenOCD config file
            "usb_port": usb_port,  # e.g., "1-1.3"
            "status": "idle"
        }

        self.save_inventory()


    #remove host
    def remove_host(self, hostname):
        if hostname in self.inventory["all"]["hosts"]:
            del self.inventory["all"]["hosts"][hostname]
            self.save_inventory()
            return True
        return False


    #refresh host status from device host api
    def refresh_host_status(self, hostname: str):
        host = self.inventory["all"]["hosts"][hostname]

        # Use HOST_AGENT_URL or fallback to device IP
        host_agent_url = get_host_agent_url()
        if host_agent_url and not host_agent_url.startswith("http://localhost"):
            base_url = host_agent_url.rstrip("/")
        else:
            ip = host.get("ansible_host", "localhost")
            base_url = f"http://{ip}:8010"

        try:
            # Pull host health and DUT details
            health = requests.get(f"{base_url}/health", timeout=HTTP_TIMEOUT_S).json()
            duts_resp = requests.get(f"{base_url}/duts", timeout=HTTP_TIMEOUT_S).json()

            # Status normalizing
            health_status = health.get("status", "healthy")
            host["status"] = "idle" if health_status == "healthy" else health_status
            host["last_seen_epoch"] = int(time.time())

            items = duts_resp.get("items")

            if isinstance(items, list):
                normalized = []
                status_counts = {"running": 0, "idle": 0, "offline": 0}
                types = []

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

                host["duts"] = {
                    "count": len(normalized),
                    "types": sorted(set(types)),
                    "items": normalized,
                    "status_counts": status_counts,
                }

            else:
                # Fallback mode: simpler shape
                count = int(duts_resp.get("count", 0))
                types = list(duts_resp.get("types", []))

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
                    "status_counts": {"running": 0, "idle": count, "offline": 0},
                }

            self.save_inventory()
            return host

        except requests.exceptions.RequestException:
            host["status"] = "disconnected"
            host["last_seen_epoch"] = int(time.time())
            self.save_inventory()
            return host


    #refresh hosts
    def refresh_all_statuses(self):
        return {h: self.refresh_host_status(h) for h in self.list_hosts()}


    #inventory summary
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
