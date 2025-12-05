# logic for tests

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import re
import requests

from core.device_manage import DeviceManager


class TestManager:
    def __init__(self):
        # { test_id: {
        #   "name": str,
        #   "description": str,
        #   "status": str,
        #   "started_at": iso,
        #   "finished_at": iso|None,
        #   "test_duration": str,
        #   "expires_at": iso|None,
        #   "test_config": dict,
        #   "logs": [str],
        #   "serial_logs": dict,
        #   "serial_streams": dict,
        #   "dut_images": dict,
        #   "device_hosts": list
        # } }
        self.tests: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1


    #parse duration
    def _parse_duration(self, duration_str: str) -> timedelta:
        """Parse duration like '1d 2h 30m' into timedelta."""
        days = hours = minutes = 0

        day_match = re.search(r'(\d+)d', duration_str)
        hour_match = re.search(r'(\d+)h', duration_str)
        min_match = re.search(r'(\d+)m', duration_str)

        if day_match: days = int(day_match.group(1))
        if hour_match: hours = int(hour_match.group(1))
        if min_match: minutes = int(min_match.group(1))

        return timedelta(days=days, hours=hours, minutes=minutes)


    #send api call to rest agent
    def _send_flash_request(self, host_ip: str, image_path: str, openocd_cfg: str):
        """Send REST POST request to Pi agent to flash firmware."""
        url = f"http://{host_ip}:8010/flash"
        payload = {
            "image_path": image_path,
            "openocd_cfg": openocd_cfg
        }

        try:
            resp = requests.post(url, json=payload, timeout=30)
            return resp.json()
        except Exception as e:
            return {
                "returncode": 1,
                "stderr": f"REST failure: {str(e)}",
                "stdout": ""
            }


    #flash dut with restAPI point
    def _flash_all_duts(self, test_id: int) -> bool:
        test = self.tests[test_id]
        dut_images = test.get("dut_images", {})

        dm = DeviceManager()

        test["logs"].append(
            f"[{datetime.utcnow().isoformat()}] Sending flash requests to Device Hosts..."
        )

        for host, dut_dict in dut_images.items():
            try:
                host_ip = dm.get_hosts()[host]["ansible_host"]
            except KeyError:
                test["logs"].append(f"[Flash] ERROR: Host '{host}' not found in inventory.")
                return False

            openocd_cfg = dut_dict.get("openocd_cfg")
            if not openocd_cfg:
                test["logs"].append(f"[Flash] ERROR: No openocd_cfg for '{host}'.")
                return False

            for dut_name, image_path in dut_dict.items():
                if dut_name == "openocd_cfg":
                    continue  # skip cfg key

                result = self._send_flash_request(host_ip, image_path, openocd_cfg)

                if result.get("returncode") == 0:
                    test["logs"].append(
                        f"[Flash] SUCCESS: {dut_name} flashed on {host}"
                    )
                else:
                    test["logs"].append(
                        f"[Flash] ERROR: {dut_name} on {host}\n"
                        f"STDERR: {result.get('stderr')}"
                    )
                    test["status"] = "failed"
                    test["finished_at"] = datetime.utcnow().isoformat()
                    return False

        test["logs"].append(
            f"[{datetime.utcnow().isoformat()}] Flashing complete."
        )
        return True


    #start test
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

        # Parse test YAML structure
        if test_config:
            description = test_config.get("Job", {}).get("description", "")
            test_duration_str = test_config.get("test_duration")

            # Firmware section
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

            # Expiration calculation
            if test_duration_str:
                duration = self._parse_duration(test_duration_str)
                expires_at = (now + duration).isoformat()

        # Create test entry
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

        #flash dut
        flash_success = self._flash_all_duts(test_id)

        if not flash_success:
            fail_time = datetime.utcnow().isoformat()
            self.tests[test_id]["status"] = "failed"
            self.tests[test_id]["finished_at"] = fail_time
            self.tests[test_id]["logs"].append(
                f"[{fail_time}] Test failed due to flashing error."
            )
            self.next_id += 1
            return test_id

        # Normal continuation
        self.next_id += 1
        return test_id


    #stop test
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


    #retrieve log
    def get_test_logs(self, test_id: int, log_type: str = "all") -> Optional[Dict[str, Any]]:
        test = self.tests.get(test_id)
        if not test:
            return None

        result = {
            "test_id": test_id,
            "name": test["name"],
            "status": test["status"],
            "started_at": test["started_at"],
            "finished_at": test["finished_at"],
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


    #test lookup
    def get_tests(self) -> dict:
        return self.tests

    def get_test(self, test_id: int) -> Optional[dict]:
        return self.tests.get(test_id)

    def is_test_expired(self, test_id: int) -> bool:
        test = self.tests.get(test_id)
        if not test or not test.get("expires_at"):
            return False

        expires_at = datetime.fromisoformat(test["expires_at"])
        return datetime.utcnow() > expires_at


