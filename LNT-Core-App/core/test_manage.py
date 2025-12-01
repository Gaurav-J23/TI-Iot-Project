# logic for tests

from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import re
from flashing.openocd_flash import OpenOCDFlasher


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
        #   "serial_logs": dict,
        #   "serial_streams": dict,
        #   "dut_images": dict,
        #   "device_hosts": List[str]
        # } }
        self.tests: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1

    def _parse_duration(self, duration_str: str) -> timedelta:
        """Parse duration string like '1d 2h 30m' into timedelta."""
        days = 0
        hours = 0
        minutes = 0

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

    #Flash all DUTs listed in the test config using OpenOCD.
    #Expects each DUT host in inventory/test_config to include:
    #"openocd_cfg": "/etc/openocd/boards/cc26x2.cfg"
    def _flash_all_duts(self, test_id: int) -> bool:

        test = self.tests[test_id]
        dut_images = test.get("dut_images", {})

        flasher = OpenOCDFlasher()

        test["logs"].append(f"[{datetime.utcnow().isoformat()}] Starting OpenOCD flashing...")

        for host, dut_dict in dut_images.items():

            # the DUT dict should contain:
            #   { "dut1": "path/to/image.bin", "openocd_cfg": "/etc/openocd/boards/cc26x2.cfg" }
            openocd_cfg = dut_dict.get("openocd_cfg")

            if not openocd_cfg:
                test["logs"].append(
                    f"[Flash] ERROR: No 'openocd_cfg' provided for host '{host}'. Skipping flashing."
                )
                return False

            # flash every DUT entry except openocd_cfg
            for dut_name, image_path in dut_dict.items():
                if dut_name == "openocd_cfg":
                    continue

                result = flasher.flash(image_path, openocd_cfg)

                if result["returncode"] == 0:
                    test["logs"].append(
                        f"[Flash] SUCCESS: {dut_name} on {host} flashed successfully."
                    )
                else:
                    test["logs"].append(
                        f"[Flash] ERROR: Failed to flash {dut_name} on {host}.\n"
                        f"STDERR: {result['stderr']}"
                    )
                    test["status"] = "failed"
                    test["finished_at"] = datetime.utcnow().isoformat()
                    return False

        test["logs"].append(f"[{datetime.utcnow().isoformat()}] Flashing complete.")
        return True

    #Starting test
    def start_test(self, name: str, test_config: Optional[Dict[str, Any]] = None,
                   test_yaml_path: Optional[str] = None) -> int:

        test_id = self.next_id
        now = datetime.utcnow()

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

            # DUT firmware section
            firmware = test_config.get("Firmwrare", {}) or test_config.get("Firmware", {})
            for host_name in firmware.keys():
                if host_name not in device_hosts:
                    device_hosts.append(host_name)
                dut_images[host_name] = firmware.get(host_name, {})

            # Serial streams
            serial_streams_config = test_config.get("serial_steams", {}) or test_config.get("serial_streams", {})
            for host_name, streams in serial_streams_config.items():
                if host_name not in device_hosts:
                    device_hosts.append(host_name)
                serial_streams[host_name] = streams

            # Serial logs
            serial_logs_config = test_config.get("serial_logs", {})
            for host_name, logs in serial_logs_config.items():
                if host_name not in device_hosts:
                    device_hosts.append(host_name)
                serial_logs[host_name] = logs

            # Expiration
            if test_duration_str:
                duration = self._parse_duration(test_duration_str)
                expires_at = (now + duration).isoformat()

        # Store test entry
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

        #flash step before test starts
        flash_success = self._flash_all_duts(test_id)

        if not flash_success:
            # If flashing fails, the test fails immediately
            fail_time = datetime.utcnow().isoformat()
            self.tests[test_id]["status"] = "failed"
            self.tests[test_id]["finished_at"] = fail_time
            self.tests[test_id]["logs"].append(f"[{fail_time}] Test failed due to flashing error.")
            self.next_id += 1
            return test_id

        # Continue normal start
        self.next_id += 1
        return test_id

    #stopping test
    def stop_test(self, test_id: int, reason: str = "stopped") -> bool:
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

    #obtaining logs
    def get_test_logs(self, test_id: int, log_type: str = "all") -> Optional[Dict[str, Any]]:
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

    #update test
    def update_test(self, test_id: int, status: str | None = None, log: str | None = None,
                    serial_log: Optional[Dict[str, str]] = None,
                    stream_update: Optional[Dict[str, Any]] = None) -> dict | None:

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
        return self.tests

    def get_test(self, test_id: int) -> dict | None:
        return self.tests.get(test_id)

    def is_test_expired(self, test_id: int) -> bool:
        test = self.tests.get(test_id)
        if not test or not test.get("expires_at"):
            return False

        expires_at = datetime.fromisoformat(test["expires_at"])
        return datetime.utcnow() > expires_at

