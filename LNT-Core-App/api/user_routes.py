# user_routes.py
from fastapi import APIRouter, HTTPException
from core.user_manage import UserManager

router = APIRouter()
user_manage = UserManager()

# --------------------------------------
# LOGIN
# --------------------------------------
@router.post("/login")
def login(username: str, password: str):
    if user_manage.authenticate(username, password):
        user = user_manage.get_user(username)
        return {
            "message": "Login successful!",
            "username": username,
            "roles": user.roles
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --------------------------------------
# LIST USERS
# --------------------------------------
@router.get("/list")
def list_users():
    users = user_manage.get_users()
    return {"users": users}

# --------------------------------------
# ADD USER
# --------------------------------------
@router.post("/add")
def add_user(username: str, password: str, role: str = "user"):
    # Prevent overwriting admin accidentally
    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot overwrite the admin user.")

    if username in user_manage.get_users():
        raise HTTPException(status_code=400, detail="User already exists.")

    user_manage.add_user(username, password, roles=[role])
    return {"message": f"User '{username}' created.", "roles": [role]}

# --------------------------------------
# REMOVE USER
# --------------------------------------
@router.post("/remove")
def remove_user(username: str):
    if username == "admin":
        raise HTTPException(status_code=400, detail="Cannot remove the admin user.")

    success = user_manage.remove_user(username)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"message": f"User '{username}' removed."}

# --------------------------------------
# UPDATE USER ROLE
# --------------------------------------
@router.post("/set-role")
def set_role(username: str, role: str):
    user = user_manage.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Assign new single role
    user.roles = [role]
    user_manage._save_to_yaml()

    return {"message": f"Role for '{username}' updated.", "roles": user.roles}
