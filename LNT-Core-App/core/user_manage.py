# logic for users (in-memory + YAML persistence)

from dataclasses import dataclass
from typing import Dict, Optional, List
import yaml
import os

@dataclass
class _User:
    username: str
    password: str  # plain text for now to keep it simple (swap to hashed later)
    roles: List[str]

class UserManager:
    def __init__(self, yaml_path="core/data/users.yml"):
        self.yaml_path = yaml_path
        self._users: Dict[str, _User] = {}

        # NEW: load users from YAML
        self._load_from_yaml()

        # If YAML has no users, seed default admin
        if not self._users:
            self._users = {
                "admin": _User(username="admin", password="admin123", roles=["admin"])
            }
            self._save_to_yaml()

    # -------------------------------
    # This is to save user files to yamal
    # -------------------------------
    def _load_from_yaml(self):
        """Loads users from YAML file if it exists."""
        if os.path.exists(self.yaml_path):
            with open(self.yaml_path, "r") as f:
                data = yaml.safe_load(f) or {}
                users_dict = data.get("users", {})
                for uname, info in users_dict.items():
                    self._users[uname] = _User(
                        username=uname,
                        password=info["password"],
                        roles=info.get("roles", ["user"])
                    )

    def _save_to_yaml(self):
        """Saves current users to YAML file."""
        data = {
            "users": {
                uname: {
                    "password": u.password,
                    "roles": u.roles
                }
                for uname, u in self._users.items()
            }
        }
        os.makedirs(os.path.dirname(self.yaml_path), exist_ok=True)
        with open(self.yaml_path, "w") as f:
            yaml.dump(data, f)



    # --- auth ---
    def authenticate(self, username: str, password: str) -> bool:
        u = self._users.get(username)
        return bool(u and u.password == password)

    # --- queries ---
    def get_users(self) -> list[str]:
        return list(self._users.keys())

    def get_user(self, username: str) -> Optional[_User]:
        return self._users.get(username)

    # --- admin ops ---
    def add_user(self, username: str, password: str, roles: Optional[List[str]] = None) -> None:
        self._users[username] = _User(
            username=username,
            password=password,
            roles=roles or ["user"]
        )
        self._save_to_yaml()  # NEW

    def set_password(self, username: str, new_password: str) -> bool:
        u = self._users.get(username)
        if not u:
            return False
        u.password = new_password
        self._save_to_yaml()  # NEW
        return True

    def remove_user(self, username: str) -> bool:
        """Remove a user from the system. Returns True if user was removed, False if user doesn't exist."""
        if username in self._users:
            del self._users[username]
            self._save_to_yaml()  # NEW
            return True
        return False
