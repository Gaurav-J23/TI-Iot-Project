# logic for tests

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import re

class TestManager:
    def __init__(self):
        # { test_id: { 
        #   "name": str, 
        #   "description": str,
        #   "status": str, 
        #   "started_at": iso, 
        #   "finished_at": iso|None, 
        #   "test_duration": str (e.g., "1d 2h 30m"),
        #   "expires_at": iso|None,
        #   "test_config": dict (parsed test.yaml),
        #   "logs": [str],
        #   "serial_logs": dict,  # { "host": { "port": "log_file_path" } }
        #   "serial_streams": dict,  # { "host": { "port": stream_data } }
        #   "dut_images": dict,  # { "host": { "dut_name": "image_path" } }
        #   "device_hosts": List[str]  # List of device hosts involved
        # } }
        self.tests: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1

    def _parse_duration(self, duration_str: str) -> timedelta:
        """Parse duration string like '1d 2h 30m' into timedelta."""
        days = 0
        hours = 0
        minutes = 0
        
        # Match patterns like "1d", "2h", "30m"
        day_match = re.search(r'(\d+)d', duration_str)
        hour_match = re.search(r'(\d+)h', duration_str)
        min_match = re.search(r'(\d+)m', duration_str)
        
        if day_match:
            days = int(day_match.group(1))
        if hour_match:
            hours = int(hour_match.group(1))
        if min_match:
            minutes = int(min_match.group(1))
        
        return timedelta(days=days, hours=hours, minutes=minutes)

    def start_test(self, name: str, test_config: Optional[Dict[str, Any]] = None, 
                   test_yaml_path: Optional[str] = None) -> int:
        """
        Start a new test. Can accept either a test_config dict (parsed YAML) or test_yaml_path.
        
        Args:
            name: Test name
            test_config: Parsed test.yaml configuration dict
            test_yaml_path: Path to test.yaml file (for future file parsing)
        
        Returns:
            test_id: Unique test identifier
        """
        test_id = self.next_id
        now = datetime.utcnow()
        
        # Parse test configuration
        description = ""
        test_duration_str = None
        expires_at = None
        device_hosts = []
        dut_images = {}
        serial_streams = {}
        serial_logs = {}
        
        if test_config:
            description = test_config.get("Job", {}).get("description", "")
            test_duration_str = test_config.get("test_duration")
            
            # Extract device hosts from firmware section
            firmware = test_config.get("Firmwrare", {}) or test_config.get("Firmware", {})
            for host_name in firmware.keys():
                if host_name not in device_hosts:
                    device_hosts.append(host_name)
                dut_images[host_name] = firmware.get(host_name, {})
            
            # Extract serial streams configuration
            serial_streams_config = test_config.get("serial_steams", {}) or test_config.get("serial_streams", {})
            for host_name, streams in serial_streams_config.items():
                if host_name not in device_hosts:
                    device_hosts.append(host_name)
                serial_streams[host_name] = streams
            
            # Extract serial logs configuration
            serial_logs_config = test_config.get("serial_logs", {})
            for host_name, logs in serial_logs_config.items():
                if host_name not in device_hosts:
                    device_hosts.append(host_name)
                serial_logs[host_name] = logs
            
            # Calculate expiration time
            if test_duration_str:
                duration = self._parse_duration(test_duration_str)
                expires_at = (now + duration).isoformat()
        
        self.tests[test_id] = {
            "name": name,
            "description": description,
            "status": "running",
            "started_at": now.isoformat(),
            "finished_at": None,
            "test_duration": test_duration_str,
            "expires_at": expires_at,
            "test_config": test_config or {},
            "test_yaml_path": test_yaml_path,
            "logs": [f"[{now.isoformat()}] Started test '{name}'"],
            "serial_logs": serial_logs,
            "serial_streams": serial_streams,
            "dut_images": dut_images,
            "device_hosts": device_hosts
        }
        self.next_id += 1
        return test_id

    def stop_test(self, test_id: int, reason: str = "stopped") -> bool:
        """
        Stop a running test.
        
        Args:
            test_id: Test identifier
            reason: Reason for stopping (e.g., "stopped", "cancelled")
        
        Returns:
            True if test was stopped, False if test doesn't exist or already finished
        """
        test = self.tests.get(test_id)
        if not test:
            return False
        
        if test["status"] not in ("running", "pending"):
            return False
        
        now = datetime.utcnow().isoformat()
        test["status"] = "cancelled" if reason == "cancelled" else "stopped"
        test["finished_at"] = now
        test["logs"].append(f"[{now}] Test {reason} by user")
        return True

    def get_test_logs(self, test_id: int, log_type: str = "all") -> Optional[Dict[str, Any]]:
        """
        Get logs for a specific test run.
        
        Args:
            test_id: Test identifier
            log_type: Type of logs to retrieve - "all", "text", "serial", "streams"
        
        Returns:
            Dict containing requested logs, or None if test doesn't exist
        """
        test = self.tests.get(test_id)
        if not test:
            return None
        
        result = {
            "test_id": test_id,
            "name": test["name"],
            "status": test["status"],
            "started_at": test["started_at"],
            "finished_at": test["finished_at"]
        }
        
        if log_type in ("all", "text"):
            result["text_logs"] = test["logs"]
        
        if log_type in ("all", "serial"):
            result["serial_logs"] = test["serial_logs"]
        
        if log_type in ("all", "streams"):
            result["serial_streams"] = test["serial_streams"]
        
        return result

    def update_test(self, test_id: int, status: str | None = None, log: str | None = None,
                   serial_log: Optional[Dict[str, str]] = None,
                   stream_update: Optional[Dict[str, Any]] = None) -> dict | None:
        """
        Update test status and/or add log entries.
        
        Args:
            test_id: Test identifier
            status: New status (e.g., "running", "passed", "failed", "cancelled")
            log: Text log entry to add
            serial_log: Dict with {"host": {"port": "log_file_path"}} for serial log updates
            stream_update: Dict with {"host": {"port": stream_data}} for stream data updates
        
        Returns:
            Updated test dict or None if test doesn't exist
        """
        test = self.tests.get(test_id)
        if not test:
            return None
        
        now = datetime.utcnow().isoformat()
        
        if log:
            test["logs"].append(f"[{now}] {log}")
        
        if serial_log:
            for host, logs in serial_log.items():
                if host not in test["serial_logs"]:
                    test["serial_logs"][host] = {}
                test["serial_logs"][host].update(logs)
        
        if stream_update:
            for host, streams in stream_update.items():
                if host not in test["serial_streams"]:
                    test["serial_streams"][host] = {}
                test["serial_streams"][host].update(streams)
        
        if status:
            test["status"] = status
            if status in ("passed", "failed", "cancelled", "stopped") and test["finished_at"] is None:
                test["finished_at"] = now
                test["logs"].append(f"[{now}] Test {status}")
        
        return test

    def get_tests(self) -> dict:
        """Get all tests."""
        return self.tests

    def get_test(self, test_id: int) -> dict | None:
        """Get a specific test by ID."""
        return self.tests.get(test_id)
    
    def is_test_expired(self, test_id: int) -> bool:
        """Check if a test has expired based on its test_duration."""
        test = self.tests.get(test_id)
        if not test or not test.get("expires_at"):
            return False
        
        expires_at = datetime.fromisoformat(test["expires_at"])
        return datetime.utcnow() > expires_at
