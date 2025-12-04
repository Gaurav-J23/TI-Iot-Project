from fastapi import FastAPI
from api import device_routes, test_routes, user_routes
from dotenv import load_dotenv
from core.test_manage import TestManager
import os
from fastapi.middleware.cors import CORSMiddleware
# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="LNT App Core Service")
app.state.tm = TestManager()

# Create TestManager instance for the frontend to work
@app.on_event("startup")
def startup_event():
    app.state.tm = TestManager()

# include route modules
app.include_router(device_routes.router, prefix="/device", tags=["Device"])
app.include_router(test_routes.router, prefix="/test", tags=["Test"])
app.include_router(user_routes.router, prefix="/user", tags=["User"])

@app.get("/")
def root():
    return {"message": "LNT App Core is running!"}

# CORS for the front end to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
