# actual logic for devices

class DeviceManager:
    def __init__(self):
        self.hosts = []

    def add_host(self, hostname):
        """Add a device host to the system."""
        if hostname not in self.hosts:
            self.hosts.append(hostname)

    def remove_host(self, hostname):
        """Remove a device host from the system. Returns True if removed, False if not found."""
        if hostname in self.hosts:
            self.hosts.remove(hostname)
            return True
        return False

    def get_hosts(self):
        return self.hosts
