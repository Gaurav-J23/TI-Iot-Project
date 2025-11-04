# actual logic for devices
import yaml
import os
from utils.ansible_runner import provision_host

INVENTORY_PATH = "ansible/inventory.yml"

class DeviceManager:
    def __init__(self):
        self.inventory = self.load_inventory()

    #SOME HELPER METHODS
    #load device inventory from inventory.yml file
    def load_inventory(self):
        if not os.path.exists(INVENTORY_PATH):
            return {"all": {"hosts": {}}}
        with open(INVENTORY_PATH, "r") as f:
            return yaml.safe_load(f) or {"all": {"hosts": {}}}

    #writes current python object back to inventory.yml
    def save_inventory(self):
        with open(INVENTORY_PATH, "w") as f:
            yaml.dump(self.inventory, f)

    #returns a list of all hosts in inventory
    def list_hosts(self):
        return list(self.inventory["all"]["hosts"].keys())


    #adds new device host
    def add_host(self, hostname,ip_address):

       self.inventory["all"]["hosts"][hostname] = {
           "ansible_host": ip_address,
           "status": "pending"
       }
       self.save_inventory()
        #need to also provision

    #gets new device host
    def get_hosts(self):
        return self.hosts

    #removes device hosts
    #def remove_hosts(self, hostname, ip_address):
