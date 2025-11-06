from dataclasses import dataclass
from typing import Dict, Optional, List

@dataclass
class _User:
    username: str
    password: str  # plain text for now to keep it simple (swap to hashed later)
    roles: List[str]

class UserManager:
    def init(self):
        # seed one default user so /user/login works immediately
        self._users: Dict[str, _User] = {
            "admin": _User(username="admin", password="admin123", roles=["admin"])
        }

    # --- auth ---
    def authenticate(self, username: str, password: str) -> bool:
        u = self._users.get(username)
        return bool(u and u.password == password)

    # --- queries ---
    def get_users(self) -> list[str]:
        return list(self._users.keys())

    def get_user(self, username: str) -> Optional[_User]:
        return self._users.get(username)

    # --- admin ops (optional, handy for tests) ---
    def add_user(self, username: str, password: str, roles: Optional[List[str]] = None) -> None:
        self._users[username] = _User(username=username, password=password, roles=roles or ["user"])

    def set_password(self, username: str, new_password: str) -> bool:
        u = self._users.get(username)
        if not u:
            return False
        u.password = new_password
        return True