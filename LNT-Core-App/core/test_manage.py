# logic for tests

class TestManager:
    def __init__(self):
        self.tests = {}
        self.next_id = 1

    def start_test(self, name):
        test_id = self.next_id
        self.tests[test_id] = {"name": name, "status": "running"}
        self.next_id += 1
        return test_id

    def get_tests(self):
        return self.tests