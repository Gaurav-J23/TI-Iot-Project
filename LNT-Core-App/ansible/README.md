# Ansible Configuration for LNT Device Hosts

This directory contains Ansible playbooks and inventory files for provisioning and managing LNT device hosts.

## Files

- **inventory.yml** - Ansible inventory file defining device hosts
- **provision_host.yml** - Playbook to provision/setup device hosts
- **README.md** - This file

## Usage

### Provision a device host:
```bash
ansible-playbook -i inventory.yml provision_host.yml
```

### Provision specific host:
```bash
ansible-playbook -i inventory.yml provision_host.yml --limit LNT_DEVICE_HOST_1
```

### Test connectivity:
```bash
ansible -i inventory.yml lnt_device_hosts -m ping
```

## Prerequisites

- Ansible installed (`pip install ansible`)
- SSH access to device hosts configured
- SSH keys set up (or use `ansible_ssh_pass` in inventory)

## Device Host Setup

The provision playbook will:
- Create LNT user and directories
- Install USBIP and required packages
- Configure USBIP kernel modules
- Set up serial port permissions
- Install Python dependencies
- Create utility scripts for USBIP and serial logging

