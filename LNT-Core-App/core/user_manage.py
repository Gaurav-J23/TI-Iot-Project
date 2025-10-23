

class UserManager:
    def __init__(self):
        self.users = {"admin": "password123", "tester": "test123"}

    def authenticate(self, username, password):
        return self.users.get(username) == password

    def get_users(self):
        return list(self.users.keys())