#define user endpoints

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from core.user_manage import UserManager
from auth.jwt import create_access_token 

router = APIRouter()
user_manage = UserManager()

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(body: UserLogin):
    if not user_manage.authenticate(body.username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_access_token({"sub": body.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/list")
def list_users():
    return {"users": user_manage.get_users()}