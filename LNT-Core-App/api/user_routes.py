#define user endpoints

from fastapi import APIRouter
from core.user_manage import UserManager

router = APIRouter()
user_manage = UserManager()

@router.post("/login")
def login(username: str, password: str):
    if user_manage.authenticate(username, password):
        return {"message": "Login successful!"}
    return {"error": "Invalid credentials"}

@router.get("/list")
def list_users():
    return {"users": user_manage.get_users()}