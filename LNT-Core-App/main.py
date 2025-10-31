from fastapi import FastAPI
from api import device_routes, test_routes, user_routes
from datetime import datetime, timezone
started_at = datetime.now(timezone.utc)


app = FastAPI(title="LNT App Core Service")

# include route modules
app.include_router(device_routes.router, prefix="/device", tags=["Device"])
app.include_router(test_routes.router, prefix="/test", tags=["Test"])
app.include_router(user_routes.router, prefix="/user", tags=["User"])

@app.get("/")
def root():
    return {"message": "LNT App Core is running!"}

@app.get("/health")
def health():
    now = datetime.now(timezone.utc)
    uptime_s = (now - started_at).total_seconds()
    return {
        "status": "ok",
        "started_at": started_at.isoformat(),
        "uptime_s": int(uptime_s),
        "totals": {}  # placeholder
    }
