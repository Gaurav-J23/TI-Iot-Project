# main.py
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#routers
from api import device_routes, test_routes, user_routes

#so /health can report real numbers)
from core.device_manage import DeviceManager
from core.test_manage import TestManager
from core.user_manage import UserManager

started_at = datetime.now(timezone.utc)

app = FastAPI(title="LNT App Core Service")

# CORS so GUI can talk to the API during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# create singletons once and stash on app.state
dm = DeviceManager()
tm = TestManager()         # keep your existing constructor
um = UserManager()

app.state.dm = dm
app.state.tm = tm
app.state.um = um

# include route modules
app.include_router(device_routes.router, prefix="/device", tags=["Device"])
app.include_router(test_routes.router,  prefix="/test",   tags=["Test"])
app.include_router(user_routes.router,  prefix="/user",   tags=["User"])

@app.get("/")
def root():
    return {"message": "LNT App Core is running!"}

@app.get("/health")
def health():
    now = datetime.now(timezone.utc)
    uptime_s = int((now - started_at).total_seconds())

    # keep it simple: if a manager lacks these methods, return defaults
    device_stats = getattr(app.state.dm, "inventory_stats", lambda: {})()
    test_stats   = getattr(app.state.tm, "stats",            lambda: {})()
    user_stats   = getattr(app.state.um, "stats",            lambda: {})()

    return {
        "status": "ok",
        "started_at": started_at.isoformat(),
        "uptime_s": uptime_s,
        "devices": device_stats,   #host_count, status_counts, total_duts
        "tests":   test_stats,     # queue_len, running, finished
        "users":   user_stats,     # total_users, admins, testers
    }

