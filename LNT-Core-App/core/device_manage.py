# actual logic for devices
import yaml
import os
import time
import requests
from utils.ansible_runner import provision_host

INVENTORY_PATH = "ansible/inventory.yml"
HOST_API_PORT = 5001       # adjust to match your Device Host agent
HTTP_TIMEOUT_S = 5         # simple timeout for REST calls

class DeviceManager:
    def __init__(self):
        self.inventory = self.load_inventory()

    # SOME HELPER METHODS
    # load device inventory from inventory.yml file
    def load_inventory(self):
        if not os.path.exists(INVENTORY_PATH):
            return {"all": {"hosts": {}}}
        with open(INVENTORY_PATH, "r") as f:
            data = yaml.safe_load(f) or {}
        if "all" not in data:
            data["all"] = {}
        if "hosts" not in data["all"]:
            data["all"]["hosts"] = {}
        return data

    # writes current python object back to inventory.yml
    def save_inventory(self):
        os.makedirs(os.path.dirname(INVENTORY_PATH), exist_ok=True)
        with open(INVENTORY_PATH, "w") as f:
            yaml.safe_dump(self.inventory, f, sort_keys=True)

    # returns a list of all hosts in inventory
    def list_hosts(self):
        return list(self.inventory["all"]["hosts"].keys())

    # adds new device host (also provisions via Ansible)
    def add_host(self, hostname, ip_address):
        self.inventory["all"]["hosts"][hostname] = {
            "ansible_host": ip_address,
            "status": "pending",
            "ssh_user": "pi",
            "tags": [],
            "last_seen_epoch": 0,
            "duts": {"count": 0, "types": []},
        }
        self.save_inventory()

        # run Ansible playbook
        provision_host(
            hostname=hostname,
            ip_address=ip_address,
            inventory_path=INVENTORY_PATH,
            playbook_path="ansible/provision_host.yml",
        )

        # mark as ready; real status will be updated by refresh_host_status
        self.inventory["all"]["hosts"][hostname]["status"] = "idle"
        self.save_inventory()
        return self.inventory["all"]["hosts"][hostname]

    # gets all device hosts (full records)
    def get_hosts(self):
        return self.inventory["all"]["hosts"]

    # removes device host
    def remove_hosts(self, hostname):
        self.inventory["all"]["hosts"].pop(hostname, None)
        self.save_inventory()

    # refresh a single host's status and DUT list by calling the Device Host REST API
    # expected endpoints on the host:
    #   GET http://<ip>:<PORT>/api/health -> {"status":"idle"|"busy"}
    #   GET http://<ip>:<PORT>/api/duts   -> {"count":2,"types":["CC26x2","CC13x2"]}
    def refresh_host_status(self, hostname):
        host = self.inventory["all"]["hosts"][hostname]
        ip = host["ansible_host"]
        base = f"http://{ip}:{HOST_API_PORT}/api"

        health = requests.get(f"{base}/health", timeout=HTTP_TIMEOUT_S).json()
        duts = requests.get(f"{base}/duts", timeout=HTTP_TIMEOUT_S).json()

        host["status"] = health.get("status", "idle")
        host["last_seen_epoch"] = int(time.time())
        host["duts"] = {
            "count": int(duts.get("count", 0)),
            "types": list(duts.get("types", [])),
        }
        self.save_inventory()
        return host

    # refresh every host, return a dict of hostname -> record
    def refresh_all_statuses(self):
        return {h: self.refresh_host_status(h) for h in self.list_hosts()}

    # tiny stats block your GUI/CLI can show
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
            "last_updated_epoch": int(time.time()),
        }