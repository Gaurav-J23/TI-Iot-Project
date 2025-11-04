
import subprocess

#
def provision_host(hostname, inventory_path):
    #Run the Ansible playbook to provision a new device host.
    # Print a console log
    print(f"🚀 Provisioning host {hostname} via Ansible...")
    playbook_prov_path = "ansible/provision_host.yml"
    cmd = [
        "ansible-playbook",
        "-i", inventory_path,
        playbook_prov_path,
        "--limit", hostname
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout
