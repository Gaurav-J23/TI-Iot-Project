from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from auth.jwt import create_access_token

router = APIRouter()

class UserLogin(BaseModel):
    username: str
    password: str

class CreateUser(BaseModel):
    username: str
    password: str
    role: str = "user"

@router.post("/login")
def login(body: UserLogin, request: Request):
    um = request.app.state.um
    if not um.authenticate(body.username, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    token = create_access_token({"sub": body.username})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/list")
def list_users(request: Request):
    um = request.app.state.um
    return {"users": um.get_users()}

@router.post("/add")
def add_user(body: CreateUser, request: Request):
    um = request.app.state.um
    if um.get_user(body.username):
        raise HTTPException(status_code=400, detail="User already exists")
    um.add_user(body.username, body.password, [body.role])
    return {"message": f"User {body.username} created"}

@router.delete("/{username}")
def delete_user(username: str, request: Request):
    um = request.app.state.um
    if um.remove_user(username):
        return {"message": f"User {username} deleted"}
    raise HTTPException(status_code=404, detail="User not found")
