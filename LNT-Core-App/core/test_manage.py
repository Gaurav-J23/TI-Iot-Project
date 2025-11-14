# logic for tests
from datetime import datetime

class TestManager:
    def __init__(self):
        # { test_id: { "name": str, "status": str, "started_at": iso, "finished_at": iso|None, "logs": [str] } }
        self.tests = {}
        self.next_id = 1

    def stats(self) -> dict:
        running = sum(1 for t in self.tests.values() if t["status"] == "running")
        finished = sum(1 for t in self.tests.values() if t["status"] in ("passed", "failed", "cancelled"))
        return {
            "total_tests": len(self.tests),
            "running": running,
            "finished": finished,
        }

    def start_test(self, name: str) -> int:
        test_id = self.next_id
        now = datetime.utcnow().isoformat()
        self.tests[test_id] = {
            "name": name,
            "status": "running",
            "started_at": now,
            "finished_at": None,
            "logs": [f"[{now}] started '{name}'"]
        }
        self.next_id += 1
        return test_id

    def update_test(self, test_id: int, status: str | None = None, log: str | None = None) -> dict | None:
        test = self.tests.get(test_id)
        if not test:
            return None
        if log:
            test["logs"].append(f"[{datetime.utcnow().isoformat()}] {log}")
        if status:
            test["status"] = status
            if status in ("passed", "failed", "cancelled") and test["finished_at"] is None:
                test["finished_at"] = datetime.utcnow().isoformat()
        return test

    def get_tests(self) -> dict:
        return self.tests

    def get_test(self, test_id: int) -> dict | None:
        return self.tests.get(test_id)