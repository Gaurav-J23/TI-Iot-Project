# actual logic for devices

class DeviceManager:
    def __init__(self):
        self.hosts = []

    def add_host(self, hostname):
        self.hosts.append(hostname)

    def get_hosts(self):
        return self.hosts