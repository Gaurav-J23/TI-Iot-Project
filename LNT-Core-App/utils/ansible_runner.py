# Ansible runner utility for provisioning hosts

import subprocess
import os

def provision_host(hostname: str, inventory_path: str = "ansible/inventory.yml", playbook_path: str = "ansible/provision_host.yml"):
    """
    Run Ansible playbook to provision a device host.
    
    Args:
        hostname: Name of the host to provision
        inventory_path: Path to Ansible inventory file
        playbook_path: Path to Ansible playbook
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Run ansible-playbook with limit to specific host
        cmd = [
            "ansible-playbook",
            "-i", inventory_path,
            playbook_path,
            "--limit", hostname
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print(f"Error provisioning host {hostname}: {e}")
        return False

