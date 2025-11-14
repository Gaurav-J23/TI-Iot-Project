from datetime import datetime, timezone
from fastapi import FastAPI

# routers
from api import device_routes, test_routes, user_routes

# so /health can report real numbers
from core.device_manage import DeviceManager
from core.test_manage import TestManager
from core.user_manage import UserManager

started_at = datetime.now(timezone.utc)

app = FastAPI(title="LNT App Core Service")

# create singletons once and stash on app.state
dm = DeviceManager()
tm = TestManager()
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

    device_stats = app.state.dm.inventory_stats()
    test_stats   = app.state.tm.stats()
    user_stats   = app.state.um.stats()

    return {
        "status": "ok",
        "started_at": started_at.isoformat(),
        "uptime_s": uptime_s,
        "devices": device_stats,   # host_count, status_counts, total_duts
        "tests":   test_stats,     # total_tests, running, finished
        "users":   user_stats,     # total_users, admins
    }

